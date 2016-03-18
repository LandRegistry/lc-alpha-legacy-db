import psycopg2


def get_keyholder(connection, number):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT account_code, postcode, name_length_1, name_length_2, name, address_length_1, '
                   'address_length_2, address_length_3, address_length_4, address_length_5, address '
                   'FROM keyholders WHERE number=%(number)s', {'number': number})
    rows = cursor.fetchall()
    if len(rows) == 0:
        return None

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
        'name': row['name'],  # split_string_by_array(row['name'], name_lengths),
        'address': {
            'address_lines': split_string_by_array(row['address'], address_lengths),
            'postcode': row['postcode']
        },
        'account_code': row['account_code']
    }
    return data


def create_keyholder(connection, data):  # pragma: no cover
    number = data['number']
    account_code = data['account_code']  # "C"
    address_data = array_to_string(data['address']['address_lines'], 5)
    name_data = array_to_string(data['name'], 2)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
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


def split_string_by_array(string, array):
    result = []
    for item in array:
        extracted = string[0:item].strip()
        if extracted != "":
            result.append(extracted)
        string = string[item:]
    return result


def array_to_string(array, num):  # pragma: no cover
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
