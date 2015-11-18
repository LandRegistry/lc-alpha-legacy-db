from flask import Response, request
from flask.ext.cors import cross_origin
import psycopg2
import psycopg2.extras
import json
import logging
from application import app
from application.debtor import create_debtor_records
from application.errors import record_error
from application.names import get_name_variants
from application.landcharges import migrate, synchronise
from application.keyholders import get_keyholder, create_keyholder


@app.errorhandler(Exception)
def error_handler(err):
    logging.error('========== Error Caught ===========')
    logging.error(err)
    return Response(str(err), status=500)


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


@app.route('/errors', methods=['POST'])
def errors():
    data = request.get_json(force=True)
    record_error(data)
    return Response(status=200)


@app.route('/debtors', methods=['POST'])
def add_debtor():
    data = request.get_json(force=True)
    create_debtor_records(data, get_database_connection().cursor)
    return Response(status=200)


@app.route('/land_charges', methods=["GET"])
def get_land_charge_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if (start_date is None or start_date == '') or (end_date is None or end_date == ''):
        logging.error("Missing start_date or end_date")
        return Response("Missing start_date or end_date", status=400)

    data = migrate(get_database_connection(), start_date, end_date)
    if len(data) == 0:
        return Response(status=404)
    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/land_charges', methods=['PUT'])
def add_to_db2():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    data = request.get_json(force=True)
    connection = get_database_connection()
    return synchronise(connection, data)


@app.route('/keyholders/<number>', methods=['GET'])
@cross_origin()
def get_keyholder_route(number):
    data = get_keyholder(get_database_connection(), number)
    if data is None:
        return Response(status=404)
    else:
        return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/complex_names/search', methods=['POST'])
def search_complex_names():
    # Search based on name passed in body - some 'complex names' can be ridiculously long
    data = request.get_json(force=True)
    name = data['name']
    conn = get_database_connection()
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


@app.route('/land_charges', methods=['DELETE'])
def delete_lcs():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    conn = get_database_connection()
    conn.cursor().execute("DELETE FROM lc_mock")
    conn.commit()
    return Response(status=200)


@app.route('/complex_names', methods=['DELETE'])
def deleta_complex_names():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    conn = get_database_connection()
    conn.cursor().execute("DELETE FROM name_variants")
    conn.commit()
    return Response(status=200)


@app.route('/debtors', methods=['DELETE'])
def delete_debtors():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)

    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM debtor_court")
    cursor.execute("DELETE FROM debtor")
    cursor.execute("DELETE FROM no_hit")
    cursor.execute("DELETE FROM previous")
    cursor.execute("DELETE FROM property_detail")
    cursor.execute("DELETE FROM debtor_control")
    cursor.execute("DELETE FROM debtor_detail")
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
def create_keyholder():  # pragma: no cover
    if not app.config['ALLOW_DEV_ROUTES']:
        return Response(status=403)
    # Method only for populating test data easily...
    data = request.get_json(force=True)
    create_keyholder(get_database_connection(), data)
    return Response("Record added to db2", status=200)


def get_database_connection():
    try:
        return psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        logging.error(error)
        raise
