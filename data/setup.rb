require 'net/http'
require 'json'

keyholders = [
    '{"name": ["S & H Legal Group"], "number": 1234567, "address": {"postcode": "PP39 6BY", "county": "Newport", "address_lines": ["49 Camille Circles", "Port Eulah"]}, "account_code": "C"}',
    '{"name": ["Rice & Breitenberg"], "number": 4163351, "address": {"postcode": "FH63 1JS", "county": "Gwynedd", "address_lines": ["78 Cassidy Mission", "South Scotmouth"]}, "account_code": "C"}',
    '{"name": ["Miller, Dicki & Funk Legal Group"], "number": 3864640, "address": {"postcode": "AL22 1VH", "county": "Salop", "address_lines": ["757 Hilbert Spur", "Devonteborough"]}, "account_code": "C"}',
    '{"name": ["F & G Associates"], "number": 6960095, "address": {"postcode": "OF53 4UI", "county": "Thurrock", "address_lines": ["75 Arianna Prairie", "Kleinmouth"]}, "account_code": "C"}',
    '{"name": ["Davis & Bins Conveyancers"], "number": 2919313, "address": {"postcode": "TW42 3MT", "county": "East Sussex", "address_lines": ["21 Jaqueline Rapid", "Port Maria"]}, "account_code": "C"}',
    '{"name": ["Donnelly, Marks & Gerlach"], "number": 1357720, "address": {"postcode": "UO97 6PO", "county": "Worcestershire", "address_lines": ["397 Moore Avenue", "Howemouth"]}, "account_code": "C"}',
    '{"name": ["Jessica Smith Group"], "number": 6547023, "address": {"postcode": "NC44 8LC", "county": "Milton Keynes", "address_lines": ["70 Stehr Stream", "Harriston"]}, "account_code": "C"}',
    '{"name": ["Luettgen, Harris & Moore Conveyancers"], "number": 4709425, "address": {"postcode": "EC25 1JQ", "county": "Suffolk", "address_lines": ["747 O\'Hara Ramp", "North Maximostad"]}, "account_code": "C"}',
    '{"name": ["W & Q"], "number": 6705139, "address": {"postcode": "MI83 3BQ", "county": "West Midlands", "address_lines": ["711 Emelie Glens", "New Ibrahim"]}, "account_code": "C"}',
    '{"name": ["X & L Conveyancers"], "number": 5074699, "address": {"postcode": "DW16 4QN", "county": "Hampshire", "address_lines": ["550 Vaughn Springs", "Port Eugeneside"]}, "account_code": "C"}'
]

uri = URI(ENV['LEGACY_DB_URI'] || 'http://localhost:5007')
http = Net::HTTP.new(uri.host, uri.port)
keyholders.each do |item|
    request = Net::HTTP::Post.new('/keyholders')
    request.body = item
    request["Content-Type"] = "application/json"
    response = http.request(request)
    if response.code != "200"
        puts "legacy-db/keyholders: #{response.code}"
    end
end


cnames = [
    '{"amend": "", "date": null, "number": "1065448", "source": "", "uid": "", "name": "MOCKVILLE BISHOP OF"}',
    '{"amend": "", "date": null, "number": "1065448", "source": "", "uid": "", "name": "MOCKVILLE LORD BISHOP OF"}',
    '{"amend": "", "date": null, "number": "1066224", "source": "", "uid": "", "name": "BORERBERG VISCOUNT"}',
    '{"amend": "", "date": null, "number": "1066224", "source": "", "uid": "", "name": "ORNMOUTH VISCOUNT"}',
    '{"amend": "", "date": null, "number": "1066224", "source": "", "uid": "", "name": "BRENTTON BARON"}',
    '{"amend": "", "date": null, "number": "1066224", "source": "", "uid": "", "name": "HELENBURY BARON"}',
    '{"amend": "", "date": null, "number": "1000167", "source": "", "uid": "", "name": "KING STARK OF THE NORTH"}',
    '{"amend": "", "date": null, "number": "1000167", "source": "", "uid": "", "name": "HRH KING STARK"}',
    '{"amend": "", "date": null, "number": "1000361", "source": "", "uid": "", "name": "MERCHANTS OF THE SEA"}',
    '{"amend": "", "date": null, "number": "1000167", "source": "", "uid": "", "name": "His Royal Highness Robert Stark of Winterfell and King in the North"}'
]

cnames.each do |item|
    request = Net::HTTP::Post.new('/complex_names')
    request.body = item
    request["Content-Type"] = "application/json"
    response = http.request(request)
    if response.code != "200"
        puts "legacy-db/complex_names: #{response.code}"
    end
end