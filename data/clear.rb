require 'net/http'
require 'json'


uri = URI(ENV['LEGACY_DB_URI'] || 'http://localhost:5007')
http = Net::HTTP.new(uri.host, uri.port)
response = http.request(Net::HTTP::Delete.new('/keyholders'))
response = http.request(Net::HTTP::Delete.new('/debtors'))
response = http.request(Net::HTTP::Delete.new('/complex_names'))
response = http.request(Net::HTTP::Delete.new('/land_charges'))
response = http.request(Net::HTTP::Delete.new('/documents'))
response = http.request(Net::HTTP::Delete.new('/history'))
