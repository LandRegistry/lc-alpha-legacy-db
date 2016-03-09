from flask import Response, request
import psycopg2
import psycopg2.extras
import json
import logging
from datetime import datetime, timedelta
from application import app
from application.debtor import create_debtor_records, delete_all_debtors
from application.errors import record_error
from application.names import get_name_variants, get_name_variants_by_number
from application.landcharges import synchronise, get_all_land_charges, get_land_charge_record, get_document_record, \
    get_document_history, insert_document, insert_history_notes, delete_land_charge, get_all_land_charges_by_range
from application.keyholders import get_keyholder, create_keyholder
from application.images import create_update_image, remove_image, retrieve_image

#
# @app.errorhandler(Exception)
# def error_handler(err):
#     logging.error('========== Error Caught ===========')
#     logging.error(err)
#     return Response(str(err), status=500)


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)


@app.route('/health', methods=['GET'])
def health():
    result = {
        'status': 'OK',
        'dependencies': {}
    }
    return Response(json.dumps(result), status=200, mimetype='application/json')

# =========== ERRORS ==============


@app.route('/errors', methods=['POST'])
def errors():
    data = request.get_json(force=True)
    record_error(data)
    return Response(status=200)

# =========== DEBTORS =============


@app.route('/debtors', methods=['POST'])
def add_debtor():
    data = request.get_json(force=True)
    create_debtor_records(data, get_database_connection().cursor)
    return Response(status=200)

# =========== IMAGES ================


@app.route('/images/<date>/<regn_no>/<image_index>', methods=['GET'])
def get_image(date, regn_no, image_index):
    data = retrieve_image(app, date, regn_no, image_index)
    if data is None:
        return Response(status=404)
    return data


@app.route('/images/<date>/<regn_no>/<image_index>', methods=['DELETE'])
def delete_image(date, regn_no, image_index):
    status = remove_image(app, date, regn_no, image_index)
    if status is None:
        return Response(status=404)
    return Response(status=200)


@app.route('/images/<date>/<regn_no>/<image_index>/<size>', methods=['PUT'])
def create_or_replace_image(date, regn_no, image_index, size):
    return create_update_image(app, date, regn_no, image_index)


# =========== LAND_CHARGES =============


@app.route('/land_charges/<from_date>/<to_date>', methods=['GET'])
def get_land_charges_date_range(from_date, to_date):
    data = get_all_land_charges_by_range(get_database_connection(), from_date, to_date)
    if len(data) == 0:
        return Response(status=404)
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/land_charges', methods=['GET'])
def get_land_charges():
    type_filter = ''
    if 'type' in request.args:
        type_filter = request.args['type']

    data = get_all_land_charges(get_database_connection(), type_filter)
    if len(data) == 0:
        return Response(status=404)
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/land_charges/<number>', methods=['GET'])
def get_land_charge(number):
    if 'class' not in request.args or 'date' not in request.args:
        return Response("No class or date specified", status=400)

    data = get_land_charge_record(get_database_connection(), number, request.args['class'], request.args['date'])
    if len(data) == 0:
        return Response(status=404)
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/land_charges', methods=['PUT'])
def add_to_db2():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    data = request.get_json(force=True)
    logging.debug('-------------------------------------------')
    logging.info(data)
    connection = get_database_connection()
    return synchronise(connection, data)


@app.route('/land_charges/<number>/<date>/<class_of_charge>', methods=['DELETE'])
def delete_lc_row(number, date, class_of_charge):
    logging.info('DELETE %s %s %s', number, date, class_of_charge)

    conn = get_database_connection()
    delete_land_charge(conn.cursor(), number, date, class_of_charge)
    conn.commit()
    return Response(status=200)


@app.route('/doc_info/<number>', methods=['GET'])
def get_doc_info(number):
    if 'class' not in request.args or 'date' not in request.args:
        return Response("No class or date specified", status=400)

    data = get_document_record(get_database_connection(), number, request.args['class'], request.args['date'])
    if len(data) == 0:
        return Response(status=404)
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/doc_info/<number>/<date>/<class_of_charge>', methods=['PUT'])
def insert_new_doc_entry(number, date, class_of_charge):
    logging.info('INSERT-DOC %s %s %s', number, date, class_of_charge)
    conn = get_database_connection()
    insert_document(conn.cursor(), number, date, class_of_charge, request.get_json(force=True))
    conn.commit()
    return Response(status=200)


@app.route('/doc_history/<number>', methods=['GET'])
def get_doc_history(number):
    if 'class' not in request.args or 'date' not in request.args:
        return Response("No class or date specified", status=400)

    data = get_document_history(get_database_connection(), number, request.args['class'], request.args['date'])
    if len(data) == 0:
        return Response(status=404)
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/history_notes/<number>/<date>/<class_of_charge>', methods=['POST'])
def insert_history_note(number, date, class_of_charge):
    logging.info('INSERT-NOTE %s %s %s', number, date, class_of_charge)
    conn = get_database_connection()
    insert_history_notes(conn.cursor(), number, date, class_of_charge, request.get_json(force=True))
    conn.commit()
    return Response(status=200)


# =========== KEYHOLDERS =============


@app.route('/keyholders/<number>', methods=['GET'])
def get_keyholder_route(number):
    data = get_keyholder(get_database_connection(), number)
    if data is None:
        return Response(status=404)
    else:
        return Response(json.dumps(data), status=200, mimetype='application/json')

# =========== COMPLEX_NAMES =============


@app.route('/complex_names/search', methods=['POST'])
def search_complex_names():
    # Search based on name passed in body - some 'complex names' can be ridiculously long
    data = request.get_json(force=True)
    name = data['name']
    conn = get_database_connection()
    if 'number' in data:
        result = get_name_variants_by_number(conn, str(data['number']))
    else:
        result = get_name_variants(conn, name)
    conn.close()
    status = 200
    if len(result) == 0:
        status = 404
    return Response(json.dumps(result), status=status, mimetype='application/json')


@app.route('/complex_names/<name>', methods=['GET'])
def get_complex_names(name):
    conn = get_database_connection()
    result = get_name_variants(conn, name)
    conn.close()
    status = 200
    if len(result) == 0:
        status = 404
    return Response(json.dumps(result), status=status, mimetype='application/json')


@app.route('/complex_names', methods=['POST'])
def create_complex_name():
    data = request.get_json()
    conn = get_database_connection()
    conn.cursor().execute('INSERT INTO name_variants (amended_code, amended_date, number, source, "user", name) '
                          'VALUES (%(amend)s, %(date)s, %(num)s, %(src)s, %(user)s, %(name)s)',
                          {
                              "amend": data["amend"], "date": data["date"], "num": data["number"],
                              "src": data["source"], "user": data["uid"], "name": data["name"]
                          })
    conn.commit()
    return Response("Record added to db2", status=200)


@app.route('/dates/<date>', methods=['GET'])
def get_date_info(date):
    # Actual Legacy DB has a calendar of everything date related. Of note for us
    # are the fields for previous working day, and working day fifteen
    # days hence. We'll use that table on-network, here we'll mock the behaviour.

    # Not accounting for holidays here in dev...
    d = datetime.strptime(date, "%Y-%m-%d")
    prev_day = d - timedelta(days=1)
    fifteen = d
    thirty = d

    add_days = 14
    while add_days > 0:
        fifteen += timedelta(days=1)
        if fifteen.weekday() not in [5, 6]:
            add_days -= 1

    add_days = 29
    while add_days > 0:
        thirty += timedelta(days=1)
        if thirty.weekday() not in [5, 6]:
            add_days -= 1

    day_in_year = d.strftime("%-j").zfill(3)

    return Response(json.dumps({
        "search_expires": fifteen.strftime("%Y-%m-%d"),
        "prev_working": prev_day.strftime("%Y-%m-%d"),
        "priority_notice_expires": thirty.strftime("%Y-%m-%d"),
        "adp_date": d.strftime("%Y") + day_in_year
    }), status=200, mimetype='application/json')


# ============ DEV ROUTES ============


@app.route('/complex_names', methods=['DELETE'])
def deleta_complex_names():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    conn = get_database_connection()
    conn.cursor().execute("DELETE FROM name_variants")
    conn.commit()
    return Response(status=200)


@app.route('/keyholders', methods=['DELETE'])
def delete_keyholders():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    conn = get_database_connection()
    conn.cursor().execute("DELETE FROM keyholders")
    conn.commit()
    return Response(status=200)


@app.route('/keyholders', methods=['POST'])
def create_keyholder_route():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)
    # Method only for populating test data easily...
    data = request.get_json(force=True)
    create_keyholder(get_database_connection(), data)
    return Response("Record added to db2", status=200)


@app.route('/debtors', methods=['DELETE'])
def delete_debtors():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)
    delete_all_debtors(get_database_connection().cursor())
    return Response(status=200)


@app.route('/land_charges', methods=['POST'])
def import_land_charges():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    data = request.get_json(force=True)
    conn = get_database_connection()
    for row in data:
        conn.cursor().execute("INSERT INTO lc_mock (time, registration_no, priority_notice, reverse_name, " +
                              "property_county, registration_date, class_type, remainder_name, punctuation_code, " +
                              "name, address, occupation, counties, amendment_info, property, parish_district, " +
                              "priority_notice_ref) VALUES( %(ts)s, %(no)s, %(prio)s, %(rev)s, %(ptycounty)s, " +
                              "%(date)s, %(type)s, %(remd)s, %(punc)s, %(name)s, %(addr)s, %(occ)s, %(cty)s, " +
                              "%(amd)s, %(prop)s, %(parish)s, %(prioref)s )", {
                                  'ts': row['timestamp'],
                                  'no': row['registration_no'],
                                  'prio': row['notice'],
                                  'rev': row['coded_name'],
                                  'ptycounty': row['county'],
                                  'date': row['date'],
                                  'type': row['type'],
                                  'remd': row['remainder_name'],
                                  'punc': row['hex_code'],
                                  'name': row['complex_name'],
                                  'addr': row['address'],
                                  'occ': row['occupation'],
                                  'cty': row['county_text'],
                                  'amd': row['court_info'],
                                  'prop': row['property'],
                                  'parish': row['parish'],
                                  'prioref': row['notice_refs']
                              })
    conn.commit()
    return Response(status=200)


@app.route('/history', methods=['POST'])
def import_history():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    data = request.get_json(force=True)
    conn = get_database_connection()
    for row in data:
        conn.cursor().execute("INSERT INTO history (class, number, date, timestamp, template, text) " +
                              "VALUES( %(class)s, %(number)s, %(date)s, %(time)s, %(tmpl)s, %(text)s )", {
                                  "class": row['class'], 'number': row['reg_no'], 'date': row['reg_date'],
                                  'time': row['timestamp'], 'tmpl': row['template'], 'text': row['endt']
                              })
    conn.commit()
    return Response(status=200)


@app.route('/documents', methods=['POST'])
def import_documents():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)
    data = request.get_json(force=True)
    conn = get_database_connection()
    for row in data:
        conn.cursor().execute("INSERT INTO documents (class, number, date, orig_class, orig_number, orig_date, canc_ind, " +
                              "type, timestamp) VALUES( %(class)s, %(no)s, %(date)s, %(oclass)s, %(ono)s, %(odate)s, " +
                              "%(canc)s, %(type)s, %(ts)s )", {
                                  'class': row['class'], 'no': row['reg_no'], 'date': row['date'],
                                  'oclass': row['orig_class'], 'ono': row['orig_no'], 'odate': row['orig_date'],
                                  'canc': row['canc_ind'], 'type': row['app_type'], 'ts': row['ts']
                              })
    conn.commit()
    return Response(status=200)


@app.route('/land_charges', methods=['DELETE'])
def delete_lcs():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    conn = get_database_connection()
    conn.cursor().execute("DELETE FROM lc_mock")
    conn.commit()
    return Response(status=200)


@app.route('/history', methods=['DELETE'])
def remove_history():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)
    conn = get_database_connection()
    conn.cursor().execute("DELETE FROM history")
    conn.commit()
    return Response(status=200)


@app.route('/documents', methods=['DELETE'])
def remove_documents():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)
    conn = get_database_connection()
    conn.cursor().execute("DELETE FROM documents")
    conn.commit()
    return Response(status=200)


@app.route('/proprietors', methods=['GET'])
def get_proprietor():
    name = request.args['name']

    # This is a stub, just hard-code result
    result = [{
        'name_type': 'Private',
        'title_number': 'AB1234567',
        'prop_type': 'Sole',
        'full_name': name,
        'sub_register': 'B'
    }]
    return Response(json.dumps(result), status=200)



def get_database_connection():
    try:
        return psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        logging.error(error)
        raise
