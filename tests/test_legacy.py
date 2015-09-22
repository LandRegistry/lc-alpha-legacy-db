from application.routes import app
from unittest import mock
import os
import json
import psycopg2


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


dir = os.path.dirname(__file__)
valid_data = open(os.path.join(dir, 'data/valid_data.json'), 'r').read()
# mock_connection = MockConnection(valid_data)

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


class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect')
    def test_add_to_db2(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.put('/land_charge', data=valid_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect')
    def test_add_to_db2_invalid_data(self, mock_connect):
        headers = {'Content-Type': 'application/xml'}
        response = self.app.put('/land_charge', data=valid_data, headers=headers)
        assert response.status_code == 415

    def test_get_land_charge(self):
        response = self.app.get('/land_charge?start_date=2014-10-10&end_date=2015-03-10')
        assert response.status_code == 200

    def test_get_land_charge_no_results(self):
        response = self.app.get('/land_charge?start_date=2016-07-13&end_date=2016-07-13')
        assert response.status_code == 404

    def test_get_land_charge_missing_parameter(self):
        response = self.app.get('/land_charge?start_date=2015-07-13')
        assert response.status_code == 404

    @mock.patch('psycopg2.connect', side_effect=psycopg2.OperationalError('Fail'))
    def test_get_land_charge_fail_one(self, mock_connect):
        response = self.app.get('/land_charge?start_date=2015-07-13&end_date=2015-07-13')
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', side_effect=psycopg2.OperationalError('Fail'))
    def test_add_to_db2_fail_one(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.put('/land_charge', data=valid_data, headers=headers)
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', **keyholder_found)
    def test_get_keyholder(self, mock_connect):
        response = self.app.get('/keyholder/2365870')
        data = json.loads(response.data.decode('utf-8'))
        assert response.status_code == 200
        assert len(data['address']['address_lines']) == 3
        assert len(data['name']) == 1
        assert data['number'] == '2365870'

    @mock.patch('psycopg2.connect', **keyholder_not_found)
    def test_get_keyholder_not_found(self, mock_connect):
        response = self.app.get('/keyholder/66666')
        assert response.status_code == 404
