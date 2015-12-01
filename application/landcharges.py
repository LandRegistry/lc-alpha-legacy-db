import psycopg2
import logging
from flask import Response
import json


def migrate(connection, start_date, end_date):
    try:
        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM lc_mock where registration_date "
                       "BETWEEN %(date1)s and %(date2)s ",
                       {'date1': start_date, 'date2': end_date})

    except psycopg2.OperationalError as error:
        logging.error(error)
        raise

    rows = cursor.fetchall()
    if len(rows) == 0:
        logging.debug("No rows found")
        return []

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
    return registrations


def synchronise(connection, data):
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

    except psycopg2.OperationalError as error:
        logging.error(error)
        return Response("Failed to insert to database: {}".format(error), status=500)

    connection.commit()
    cursor.close()
    connection.close()
    return Response("Record added to db2", status=200)