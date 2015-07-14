from application import app
from flask import Response, request
import psycopg2
import json


@app.route('/', methods=["GET"])
def index():
    return Response(status=200)


@app.route('/land_charge', methods=["GET"])
def get_land_charge_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if (start_date is None or start_date == '') or (end_date is None or end_date == ''):
        return Response("Missing start_date or end_date", status=404)

    connection = get_database_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM lc_mock where registration_date "
                       "BETWEEN %(date1)s and %(date2)s ",
                       {'date1': start_date, 'date2': end_date})

    except Exception as error:
        print(error)
        return Response("Failed to select from database", status=500)

    rows = cursor.fetchall()
    if len(rows) == 0:
        return Response("No results for the search dates provided", status=404)

    registrations = []

    for db2_record in rows:
        data = {'time': db2_record[0].isoformat(),
                'registration_no': db2_record[1],
                'priority_notice': db2_record[2],
                'reverse_name': db2_record[3],
                'property_county': db2_record[4],
                'registration_date': db2_record[5].isoformat(),
                'class_type': db2_record[6],
                'remainder_name': db2_record[7],
                'punctuation_code': db2_record[8],
                'name': db2_record[9],
                'address': db2_record[10],
                'occupation': db2_record[11],
                'counties': db2_record[12],
                'amendment_info': db2_record[13],
                'property': db2_record[14],
                'parish_district': db2_record[15],
                'priority_notice_ref': db2_record[16],
                }

        registrations.append(data)
    full_data = json.dumps(registrations, ensure_ascii=False)

    return Response(full_data, status=200, mimetype='application/json')


@app.route('/land_charge', methods=['PUT'])
def add_to_db2():
    if request.headers['Content-Type'] != "application/json":
        return Response(status=415)

    data = request.get_json(force=True)

    connection = get_database_connection()

    try:
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

    except Exception as error:
        return Response("Failed to insert to database: {}".format(error), status=500)

    connection.commit()
    cursor.close()
    connection.close()
    return Response("Record added to db2", status=200)


def get_database_connection():
    try:
        return psycopg2.connect("dbname='{}' user='{}' host='{}' password='{}'".format(
            app.config['DATABASE_NAME'], app.config['DATABASE_USER'], app.config['DATABASE_HOST'],
            app.config['DATABASE_PASSWORD']))
    except Exception as error:
        return Response("Failed to connect to database: {}".format(error), status=500)