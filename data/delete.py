import os
import requests


url = os.getenv('LEGACY_ADAPTER_URI', 'http://localhost:5007')
response = requests.delete(url + '/debtors')
response = requests.delete(url + '/keyholders')
response = requests.delete(url + '/complex_names')
response = requests.delete(url + '/land_charges')
