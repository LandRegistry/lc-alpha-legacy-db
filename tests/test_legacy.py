from application.routes import app
from unittest import mock
import os
import json


class MockConnection:
    def __init__(self, results):
        self.results = results

    def cursor(self):
        return MockCursor(self.results, self)

    def commit(self):
        pass

    def close(self):
        pass


class MockCursor:
    def __init__(self, results, conn):
        self.results = results
        self.connection = conn

    def execute(self, sql, dict):
        pass

    def close(self):
        pass

    def fetchall(self):
        return self.results

    def fetchone(self):
        return [42]


dir = os.path.dirname(__file__)
valid_data = open(os.path.join(dir, 'data/valid_data.json'), 'r').read()
mock_connection = MockConnection(valid_data)


class TestWorking:
    def setup_method(self, method):
        self.app = app.test_client()

    def test_health_check(self):
        response = self.app.get("/")
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_connection)
    def test_add_to_db2(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.put('/land_charge', data=valid_data, headers=headers)
        assert response.status_code == 200

    @mock.patch('psycopg2.connect', return_value=mock_connection)
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

    @mock.patch('psycopg2.connect', side_effect=Exception('Fail'))
    def test_get_land_charge_fail_one(self, mock_connect):
        response = self.app.get('/land_charge?start_date=2015-07-13&end_date=2015-07-13')
        assert response.status_code == 500

    @mock.patch('psycopg2.connect', side_effect=Exception('Fail'))
    def test_add_to_db2_fail_one(self, mock_connect):
        headers = {'Content-Type': 'application/json'}
        response = self.app.put('/land_charge', data=valid_data, headers=headers)
        assert response.status_code == 500


