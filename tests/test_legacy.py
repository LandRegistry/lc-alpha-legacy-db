from application.routes import app
from unittest import mock
from datetime import datetime
import os
import json
import psycopg2
from application.debtor import convert_addresses, generate_id, convert_name, occupation_string, \
    convert_debtor_control, convert_debtor_details, convert_debtor_record
import re

# class MockConnection:
#     def __init__(self, results):
#         self.results = results
#
#     def cursor(self):
#         return MockCursor(self.results, self)
#
#     def commit(self):
#         pass
#
#     def close(self):
#         pass
#
#
# class MockCursor:
#     def __init__(self, results, conn):
#         self.results = results
#         self.connection = conn
#
#     def execute(self, sql, dict):
#         pass
#
#     def close(self):
#         pass
#
#     def fetchall(self):
#         return self.results
#
#     def fetchone(self):
#         return [42]


directory = os.path.dirname(__file__)
valid_data = open(os.path.join(directory, 'data/valid_data.json'), 'r').read()
lrbu_no_hits = open(os.path.join(directory, 'data/lrbu_no_hits.json'), 'r').read()
lrbu_with_hits = open(os.path.join(directory, 'data/lrbu_with_hits.json'), 'r').read()

name_variants = [
    {'number': '1234567', 'name': 'A NAME VARIANT'},
    {'number': '1234567', 'name': 'AN ALTERNATE FORM'}
]

names_found = {
    'return_value': mock.Mock(**{
        'cursor.return_value': mock.Mock(**{'fetchall.return_value': name_variants})
    })
}

names_not_found = {
    'return_value': mock.Mock(**{
        'cursor.return_value': mock.Mock(**{'fetchall.return_value': []})
    })
}

keyholder_data = [{
    'account_code': 'C',
    'postcode': 'JJ75 3SC',
    'name_length_1': 25,
    'name_length_2': 0,
    'address_length_1': 17,
    'address_length_2': 17,
    'address_length_3': 14,
    'address_length_4': 0,
    'address_length_5': 0,
    'name': 'LESSIE LITTLE ASSOCIATES ;',
    'address': '122 MAYERT TRAIL NORTH COLLINVIEW HEREFORDSHIRE ;'
}]

keyholder_found = {
    'return_value': mock.Mock(**{
        'cursor.return_value': mock.Mock(**{'fetchall.return_value': keyholder_data})
    })
}

keyholder_not_found = {
    'return_value': mock.Mock(**{
        'cursor.return_value': mock.Mock(**{'fetchall.return_value': []})
    })
}

none_found = {
    'return_value': mock.Mock(**{
        'cursor.return_value': mock.Mock(**{'fetchall.return_value': []})
    })
}

max_and_previous = {
    'return_value': mock.Mock(**{
        'cursor.return_value': mock.Mock(**{
            'fetchall.return_value': [
                {'max': 7, 'debtor_id': '2014-05-05-10:00:00.123456'}
            ],
            'fetchone.return_value': {'sequence': 7, 'date': '2015.01.01'}
        })
    })
}


legacy_data = json.loads(valid_data)
legacy_data['registration_date'] = datetime.now()
legacy_data['time'] = datetime.now()
legacy_db_data = {
    'return_value': mock.Mock(**{
        'cursor.return_value': mock.Mock(**{'fetchall.return_value': [
            legacy_data
        ]})
    })
}


class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect')
    def test_add_to_db2(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.put('/land_charges', data=valid_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect')
    def test_add_to_db2_invalid_data(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.put('/land_charges', data=valid_data, headers=headers)
        assert response.status_code == 415

    @mock.patch('psycopg2.connect', **legacy_db_data)
    def test_get_land_charge(self, mc):
        response = self.app.get('/land_charges?start_date=2014-10-10&end_date=2015-03-10')
        assert response.status_code == 200

    @mock.patch('psycopg2.connect')
    def test_get_land_charge_no_results(self, mc):
        response = self.app.get('/land_charges?start_date=2016-07-13&end_date=2016-07-13')
        assert response.status_code == 404

    @mock.patch('psycopg2.connect')
    def test_get_land_charge_missing_parameter(self, mc):
        response = self.app.get('/land_charges?start_date=2015-07-13')
        assert response.status_code == 400

    @mock.patch('psycopg2.connect', side_effect=psycopg2.OperationalError('Fail'))
    def test_get_land_charge_fail_one(self, mock_connect):
        response = self.app.get('/land_charges?start_date=2015-07-13&end_date=2015-07-13')
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', side_effect=psycopg2.OperationalError('Fail'))
    def test_add_to_db2_fail_one(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.put('/land_charges', data=valid_data, headers=headers)
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', **keyholder_found)
    def test_get_keyholder(self, mock_connect):
        response = self.app.get('/keyholders/2365870')
        data = json.loads(response.data.decode('utf-8'))
        assert response.status_code == 200
        assert len(data['address']['address_lines']) == 3
        assert len(data['name']) == 1
        assert data['number'] == '2365870'

    @mock.patch('psycopg2.connect', **keyholder_not_found)
    def test_get_keyholder_not_found(self, mock_connect):
        response = self.app.get('/keyholders/66666')
        assert response.status_code == 404

    def test_address_conversion(self):
        addresses = [
            {
                "address_lines": ['Line1', 'Line2'],
                "postcode": "Postcode1", "county": "County1"
            },
            {
                "address_lines": ['Line3', 'Line4'],
                "postcode": "Postcode2", "county": "County2"
            }
        ]
        out = convert_addresses(addresses, "*")
        assert out == 'LINE1 LINE2 POSTCODE1 COUNTY1*LINE3 LINE4 POSTCODE2 COUNTY2'

    def test_generate_id(self):
        genid = generate_id()
        match = re.match("\d{4}\-\d\d\-\d\d\-\d\d:\d\d:\d\d", genid)
        assert match is not None

    def test_convert_name(self):
        name = {
            "forenames": ["Bob", "Oscar", "Francis"],
            "surname": "Howard"
        }
        out = convert_name(name)
        assert out == "BOB OSCAR FRANCIS HOWARD"

    def test_occupation_string(self):
        record = {
            "debtor_alternative_name": [
                {
                    "forenames": ["Al", "Bob"],
                    "surname": "Smith"
                }
            ],
            "occupation": "Test case",
            "trading_name": "Unit tests"
        }
        out = occupation_string(record)
        assert out == "(N/A) AKA AL BOB SMITH T/A UNIT TESTS AS TEST CASE"

    def test_data_convert_control_no_hit(self):
        initial = json.loads(lrbu_no_hits)
        initial['registration']['search_date'] = datetime.now()
        initial['registration']['session'] = '123'
        initial['registration']['year'] = '2015'

        data = convert_debtor_control(initial['registration'], 10)
        assert data['debtor_forename'] == 'WILFRED LEW'
        assert data['debtor']['sequence'] == 10
        assert data['gender'] == 'NEUTER'
        assert data['debtor_occupation'] == '(N/A) BUTCHER'
        assert data['debtor_address'] == '1575 RUNOLFSDOTTIR LODGE EDDIEVILLE SK25 8MS DEVON'

    @mock.patch('psycopg2.connect', **none_found)
    def test_data_convert_detail_hit(self, mc):
        initial = json.loads(lrbu_with_hits)
        initial['registration']['search_date'] = datetime.now()
        initial['registration']['session'] = '123'
        initial['registration']['year'] = '2015'

        data = convert_debtor_details(mc, initial['registration'], initial['iopn'], 42)
        assert len(data['property_details']) == 11
        assert data['debtor_address'] == '875 LIBBY CLIFF NORTH MONTANA LQ45 8MD DORSET'
        assert data['action_type'] == 'PAB'
        assert data['debtor_occupation'] == '(N/A) AKA VLADIMIR FERRY HORTICULTURALIST'
        assert data['property_details'][0]['title_number'] == 'ZZ373944'

    @mock.patch('psycopg2.connect', **none_found)
    def test_debtor_route_hits(self, mc):
        initial = lrbu_with_hits
        response = self.app.post('/debtors', data=initial, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **max_and_previous)
    def test_debtor_route_no_hits(self, mc):
        initial = lrbu_no_hits
        response = self.app.post('/debtors', data=initial, headers={'Content-Type': 'application/json'})
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', **names_found)
    def test_get_names(self, mock_connect):
        response = self.app.get('/complex_names/A%20NAME')
        data = json.loads(response.data.decode('utf-8'))
        assert response.status_code == 200
        assert len(data) == 2
        assert data[0]['name'] == 'A NAME VARIANT'
        assert data[0]['number'] == '1234567'

    @mock.patch('psycopg2.connect', **names_not_found)
    def test_get_names_not_found(self, mock_connect):
        response = self.app.get('/complex_names/A%20NAME')
        assert response.status_code == 404