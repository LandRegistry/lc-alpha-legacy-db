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


@app.route('/debtor', methods=['POST'])
def add_debtor():
    data = request.get_json(force=True)
    create_debtor_records(data, get_database_connection().cursor)
    return Response(status=200)


@app.route('/land_charge', methods=["GET"])
def get_land_charge_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if (start_date is None or start_date == '') or (end_date is None or end_date == ''):
        logging.error("Missing start_date or end_date")
        return Response("Missing start_date or end_date", status=404)

    try:
        connection = get_database_connection()
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM lc_mock where registration_date "
                       "BETWEEN %(date1)s and %(date2)s ",
                       {'date1': start_date, 'date2': end_date})

    except psycopg2.OperationalError as error:
        logging.error(error)
        return Response("Failed to select from database", status=500)

    rows = cursor.fetchall()
    if len(rows) == 0:
        logging.debug("No rows found")
        return Response("No results for the search dates provided", status=404)

    registrations = []

    for db2_record in rows:
        data = {
            'time': db2_record['time'].isoformat(),
            'registration_no': db2_record['registration_no'],
            'priority_notice': db2_record['priority_notice'],
            'reverse_name': db2_record['reverse_name'],
            'property_county': db2_record['property_county'],
            'registration_date': db2_record['registration_date'].isoformat(),
            'class_type': db2_record['class_type'],
            'remainder_name': db2_record['remainder_name'],
            'punctuation_code': db2_record['punctuation_code'],
            'name': db2_record['name'],
            'address': db2_record['address'],
            'occupation': db2_record['occupation'],
            'counties': db2_record['counties'],
            'amendment_info': db2_record['amendment_info'],
            'property': db2_record['property'],
            'parish_district': db2_record['parish_district'],
            'priority_notice_ref': db2_record['priority_notice_ref'],
        }

        registrations.append(data)
    full_data = json.dumps(registrations, ensure_ascii=False)

    return Response(full_data, status=200, mimetype='application/json')


@app.route('/land_charge', methods=['PUT'])
def add_to_db2():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    try:
        data = request.get_json(force=True)
        connection = get_database_connection()

        cursor = connection.cursor()
        cursor.execute("INSERT INTO lc_mock (time, registration_no, "
                       "priority_notice, reverse_name, property_county, "
                       "registration_date, class_type, remainder_name, "
                       "punctuation_code, name, address, "
                       "occupation, counties, amendment_info, "
                       "property, parish_district, priority_notice_ref) "
                       "VALUES (%(time)s, %(registration_no)s, %(priority_notice)s, %(reverse_name)s, "
                       "%(property_county)s, %(registration_date)s, %(class_type)s, %(remainder_name)s, "
                       "%(punctuation_code)s, %(name)s, %(address)s, %(occupation)s, %(counties)s, "
                       "%(amendment_info)s, %(property)s, %(parish_district)s, %(priority_notice_ref)s) ",
                       {"time": data['time'],
                        "registration_no": data['registration_no'],
                        "priority_notice": data['priority_notice'],
                        "reverse_name": data['reverse_name'],
                        "property_county": data['property_county'],
                        "registration_date": data['registration_date'],
                        "class_type": data['class_type'],
                        "remainder_name": data['remainder_name'],
                        "punctuation_code": data['punctuation_code'],
                        "name": data['name'],
                        "address": data['address'],
                        "occupation": data['occupation'],
                        "counties": data['counties'],
                        "amendment_info": data['amendment_info'],
                        "property": data['property'],
                        "parish_district": data['parish_district'],
                        "priority_notice_ref": data['priority_notice_ref']})

    except psycopg2.OperationalError as error:
        logging.error(error)
        return Response("Failed to insert to database: {}".format(error), status=500)

    connection.commit()
    cursor.close()
    connection.close()
    return Response("Record added to db2", status=200)


@app.route('/keyholder/<number>', methods=['GET'])
@cross_origin()
def get_keyholder(number):
    cursor = get_database_connection().cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT account_code, postcode, name_length_1, name_length_2, name, address_length_1, '
                   'address_length_2, address_length_3, address_length_4, address_length_5, address '
                   'FROM keyholders WHERE number=%(number)s', {'number': number})
    rows = cursor.fetchall()
    if len(rows) == 0:
        return Response(status=404)

    # TODO: this is an assumption that the numbers are unique
    # Break address and name into arrays based on the length fields...
    row = rows[0]
    address_lengths = [
        row['address_length_1'], row['address_length_2'], row['address_length_3'], row['address_length_4'],
        row['address_length_5'],
    ]
    name_lengths = [row['name_length_1'], row['name_length_2']]
    data = {
        'number': number,
        'name': split_string_by_array(row['name'], name_lengths),
        'address': {
            'address_lines': split_string_by_array(row['address'], address_lengths),
            'postcode': row['postcode']
        },
        'account_code': row['account_code']
    }

    return Response(json.dumps(data), status=200, mimetype='application/json')


@app.route('/keyholder', methods=['POST'])
def create_keyholder():
    # Method only for populating test data easily...
    data = request.get_json(force=True)
    number = data['number']
    account_code = data['account_code']  # "C"
    address_data = array_to_string(data['address']['address_lines'], 5)
    name_data = array_to_string(data['name'], 2)
    cursor = get_database_connection().cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('INSERT INTO keyholders (number, account_code, postcode, name_length_1, name_length_2, name, '
                   'address_length_1, address_length_2, address_length_3, address_length_4, address_length_5, address) '
                   'VALUES ( %(number)s, %(account_code)s, %(postcode)s, %(name_length_1)s, %(name_length_2)s, '
                   '%(name)s, %(address_length_1)s, %(address_length_2)s, %(address_length_3)s, %(address_length_4)s, '
                   '%(address_length_5)s, %(address)s )',
                   {
                       'number': number, 'account_code': account_code, 'postcode': data['address']['postcode'],
                       'name_length_1': name_data['lengths'][0], 'name_length_2': name_data['lengths'][1],
                       'name': name_data['string'], 'address_length_1': address_data['lengths'][0],
                       'address_length_2': address_data['lengths'][1], 'address_length_3': address_data['lengths'][2],
                       'address_length_4': address_data['lengths'][3], 'address_length_5': address_data['lengths'][4],
                       'address': address_data['string']
                   })
    cursor.connection.commit()
    return Response("Record added to db2", status=200)


@app.route('/complex_names/search', methods=['POST'])
def search_complex_names():
    # Search based on name passed in body - some 'complex names' can be ridiculously long
    data = request.get_json(force=True)
    name = data['name']
    conn = get_database_connection()
    result = get_name_variants(conn, name)
    conn.close()
    return Response(json.dumps(result), status=200, mimetype='application/json')


@app.route('/complex_names/<name>', methods=['GET'])
def get_complex_names(name):
    conn = get_database_connection()
    result = get_name_variants(conn, name)
    conn.close()
    return Response(json.dumps(result), status=200, mimetype='application/json')


def array_to_string(array, num):
    lengths = []
    string = ""
    for item in array:
        lengths.append(len(item) + 1)
        string += " " + item

    while len(lengths) < num:
        lengths.append(0)

    return {
        'lengths': lengths,
        'string': string
    }


def split_string_by_array(string, array):
    result = []
    for item in array:
        extracted = string[0:item].strip()
        if extracted != "":
            result.append(extracted)
        string = string[item:]
    return result


def get_database_connection():
    try:
        return psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        logging.error(error)
        raise
