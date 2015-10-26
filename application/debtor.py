import re
from datetime import datetime
import psycopg2
import logging
import json


# The system's output ultimately needs to end up on a set of tables so the next step
# of the process can kick in. This is a legacy system with a limited userbase and
# an... interesting... set of legacy DB tables.


def generate_id():
    return datetime.now().strftime('%Y-%m-%d-%H:%M:%S.%f')


def convert_addresses(addresses, delimiter):
    output = ''
    for address in addresses:
        address_line = "{} {} {}".format(' '.join(address['address_lines']),
                                         address['postcode'], address['county'])
        if output == '':
            output = address_line
        else:
            output = "{}{}{}".format(output, delimiter, address_line)
    return output.upper()


def convert_name(name):
    return "{} {}".format(' '.join(name['forenames']), name['surname']).upper()


def occupation_string(data):
    # ("(N/A) <AKA foo>+ [T/A <trading name> AS]? <occupation>")
    n_a = "(N/A)"

    alias_names = ""
    for name in data['debtor_alternative_name']:
        alias_names += " " + convert_name(name)

    if alias_names != "":
        alias_names = " AKA" + alias_names

    if 'trading_name' in data and data['trading_name'] != '':
        occu = " T/A " + data['trading_name'] + " AS " + data['occupation']
    else:
        occu = " " + data['occupation']

    return "{}{}{}".format(n_a, alias_names, occu).upper()


def search_debtor_control(cursor, forename, surname, address):
    cursor.execute('SELECT debtor_id FROM debtor_control WHERE '
                   'address=%(addr)s AND forename=%(fn)s AND surname=%(sn)s',
                   {
                       'addr': address, 'fn': forename, 'sn': surname
                   })
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None
    else:
        return rows[0]['debtor_id']


def get_county_code(county):
    # TODO: get county code (need copy of iopn county table?)
    return 17


def get_sequence(cursor, date):
    date_str = date.strftime("%d.%m.%Y")
    cursor.execute('select MAX(sequence) FROM debtor WHERE date=%(date)s',
                   {'date': date_str})
    rows = cursor.fetchall()
    print(rows)
    if len(rows) == 0 or rows[0]['max'] is None:
        return 1
    else:
        print(rows[0])
        return int(rows[0]['max']) + 1


def convert_debtor_details(cursor, registration, iopn, sequence):
    details = {
        'reg_no': registration['registration_no'],
        'action_type': re.sub(r"\(|\)", "", registration['application_type']),
        'key_number': registration['key_number'],
        'session': registration['session'],
        'year': registration['year'],
        'date': registration['search_date'].strftime("%d.%m.%Y"),
        'status': None,
        'sequence': sequence,
        'time': registration['search_date'].strftime("%H.%M.%S"),
        'gender': 'NEUTER',
        'debtor_address': convert_addresses(registration['residence'], ' '),
        'debtor_name': convert_name(registration['debtor_name']),
        'debtor_occupation': occupation_string(registration),
        'court_name': registration['legal_body'],
        'supplementary_info': '',
        'user_id': None,
        'property_details': [],
        'no_hit': None,
        'previous': None
    }

    forename = ' '.join(registration['debtor_name']['forenames']).upper()
    surname = registration['debtor_name']['surname'].upper()
    address = convert_addresses(registration['residence'], ' ')
    previous = search_debtor_control(cursor, forename, surname, address)
    if previous is not None:
        details['previous'] = previous

    # prop detl
    prop_sequence = 1
    for hit in iopn:
        pty_info = {
            'sequence': prop_sequence,
            'app_status': 'C',  # TODO: 'P' if there are pending applications
            'pty_status': None,
            'title_message': None,  # TODO: this has lots of options. Tricky to get right,
            'assoc_appn': None,
            'title_number': hit['title_number'],
            'pty_desc': 'Property description here',  # TODO: get from relevant table (in beta)
            'prop_addr': 'Proprietor address here',  # TODO: get from relevant table (in beta)
            'prop_name': hit['full_name']
        }
        details['property_details'].append(pty_info)
        prop_sequence += 1

    # No-hit
    if len(iopn) == 0:
        if len(registration['residence']) == 0:
            logging.warning('No Residence')
            logging.warning(registration)
            county_code = 0
        else:
            county_code = get_county_code(registration['residence'][0]['county'])

        details['no_hit'] = {
            'date': registration['search_date'].strftime("%d.%m.%Y"),
            'time': registration['search_date'].strftime("%H.%M.%S"),
            'type': 'E383',  # The other types no longer happen
            'complex_no': None,
            'county_code': county_code,
            'sequence': details['sequence'],
            'gender': 'NEUTER',
            'title_number': None,
            'name': details['debtor_name']
        }
    return details


def convert_debtor_control(registration, sequence):
    debtor = {
        'date': registration['search_date'].strftime("%d.%m.%Y"),
        'sequence': sequence
    }

    court = {
        'reg_date': re.sub(r"\-", ".", registration['registration_date']),
        'reg_number': registration['registration_no'],
        'reg_type': re.sub(r"\(|\)", "", registration['application_type']),
        'key_number': registration['key_number'],
        'session': registration['session'],
        'year': registration['year'],
        'supplementary_info': None
    }

    # check details['previous'] ... might already exist
    debtor_control = {
        'complex_no': None,
        'county': get_county_code(registration['residence'][0]['county']),
        'gender': 'NEUTER',
        'complex_input': None,
        'debtor_address': convert_addresses(registration['residence'], '>'),
        'debtor_forename': ' '.join(registration['debtor_name']['forenames']).upper(),
        'debtor_occupation': '(N/A) ' + registration['occupation'].upper(),
        'debtor_surname': registration['debtor_name']['surname'].upper(),
        'debtor': debtor,
        'court': court
    }

    return debtor_control


def convert_debtor_record(cursor, data):
    registration = data['registration']
    iopn_results = data['iopn']

    legal_ref = registration['legal_body_ref']
    session = None
    if legal_ref is not None:
        match = re.match(r"(\d+) OF (\d{4})", legal_ref, re.I)
        if match:
            session = match.group(1)
            year = match.group(2)

    if session is None:
        session = 0
        year = datetime.now().strftime("%Y")

    # else:
    #     session = "0"
    #     year = "2015"  # TODO: what are we supposed to do for no-court?

    registration['search_date'] = datetime.now()
    sequence = get_sequence(cursor, registration['search_date'])
    registration['session'] = session
    registration['year'] = year

    details = convert_debtor_details(cursor, registration, iopn_results, sequence)
    control = convert_debtor_control(registration, sequence)
    return details, control


def store_control(cursor, details, control):
    if details['previous'] is None:
        control_id = generate_id()
        cursor.execute('INSERT into debtor_control (debtor_id, complex_number, county, gender, '
                       'complex_input, address, forename, occupation, surname) VALUES (%(id)s, '
                       '%(cnumber)s, %(county)s, %(gender)s, %(cinput)s, %(address)s, %(forename)s, '
                       '%(occupation)s, %(surname)s)',
                       {
                           'id': control_id, 'cnumber': control['complex_no'], 'county': control['county'],
                           'gender': control['gender'], 'cinput': control['complex_input'],
                           'address': control['debtor_address'], 'forename': control['debtor_forename'],
                           'occupation': control['debtor_occupation'], 'surname': control['debtor_surname']
                       })
    else:
        control_id = details['previous']

    cursor.execute('INSERT INTO debtor (id, date, sequence) VALUES (%(id)s, %(date)s, %(seq)s)',
                   {'id': control_id, 'date': control['debtor']['date'], 'seq': control['debtor']['sequence']})

    court = control['court']
    cursor.execute('INSERT INTO debtor_court (debtor_id, reg_date, reg_no, reg_type, key_number, session, '
                   'year, supplementary_info) VALUES (%(id)s, %(date)s, %(no)s, %(type)s, %(key)s, '
                   '%(session)s, %(year)s, %(supp)s)',
                   {
                       'id': control_id, 'date': court['reg_date'], 'no': court['reg_number'],
                       'type': court['reg_type'], 'key': court['key_number'], 'session': court['session'],
                       'year': court['year'], 'supp': court['supplementary_info']
                   })


def store_details(cursor, details):
    detail_id = generate_id()
    if details['no_hit'] is not None:
        nohit = details['no_hit']
        cursor.execute('INSERT INTO no_hit (date, time, type, complex_number, county, sequence, gender, '
                       'title_number, name) VALUES (%(date)s, %(time)s, %(type)s, %(cnumber)s, %(county)s, '
                       '%(sequence)s, %(gender)s, %(tno)s, %(name)s)',
                       {
                           'date': nohit['date'], 'time': nohit['time'], 'type': nohit['type'],
                           'cnumber': nohit['complex_no'], 'county': nohit['county_code'],
                           'sequence': nohit['sequence'], 'gender': nohit['gender'],
                           'tno': nohit['title_number'], 'name': nohit['name']
                       })
    else:
        cursor.execute('INSERT INTO debtor_detail (id, reg_no, action_type, key_no, session_no, '
                       'year, date, status, sequence_no, time, gender, debtor_address, debtor_name, '
                       'occupation, official_receiver, supplementary_info, staff_name) VALUES '
                       '( %(id)s, %(regn)s, %(action)s, %(key)s, %(session)s, %(year)s, %(date)s, '
                       '%(status)s, %(seq)s, %(time)s, %(gender)s, %(addr)s, %(name)s, %(occu)s, '
                       '%(receiver)s, %(info)s, %(user)s )',
                       {
                           'id': detail_id, 'regn': details['reg_no'], 'action': details['action_type'],
                           'key': details['key_number'], 'session': details['session'], 'year': details['year'],
                           'date': details['date'], 'status': details['status'], 'seq': details['sequence'],
                           'time': details['time'], 'gender': details['gender'], 'addr': details['debtor_address'],
                           'name': details['debtor_name'], 'occu': details['debtor_occupation'],
                           'receiver': details['court_name'], 'info': details['supplementary_info'],
                           'user': details['user_id']
                       })

        if details['previous'] is not None:
            cursor.execute('SELECT date, sequence FROM debtor WHERE id=%(id)s', {'id': details['previous']})
            row = cursor.fetchone()
            sequence = row['sequence']
            date = row['date']
            cursor.execute('INSERT INTO previous (prev_date, id, prev_seq_no) VALUES '
                           '(%(date)s, %(id)s, %(seq)s )',
                           {'date': date, 'id': detail_id, 'seq': sequence})

        for pty in details['property_details']:
            cursor.execute('INSERT INTO property_detail (id, sequence, status, prop_status, title_message, '
                           'associated_ref, title_number, description, address, name) VALUES ( %(id)s, '
                           '%(seq)s, %(status)s, %(prop)s, %(tmsg)s, %(assoc)s, %(tno)s, %(desc)s, %(addr)s, '
                           '%(name)s)',
                           {
                               'id': detail_id, 'seq': pty['sequence'], 'status': pty['app_status'],
                               'prop': pty['pty_status'], 'tmsg': pty['title_message'], 'assoc': pty['assoc_appn'],
                               'tno': pty['title_number'], 'desc': pty['pty_desc'], 'addr': pty['prop_addr'],
                               'name': pty['prop_name']
                           })


def store_debtor_record(cursor, details, control):
    store_control(cursor, details, control)
    store_details(cursor, details)


def create_debtor_records(data, cursor):
    # TODO: validate
    cursor = cursor(cursor_factory=psycopg2.extras.DictCursor)

    details, control = convert_debtor_record(cursor, data)
    store_debtor_record(cursor, details, control)

    cursor.connection.commit()
    cursor.connection.close()
