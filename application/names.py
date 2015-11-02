import psycopg2


def get_name_variants(connection, name):
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('select number from name_variants where name=%(name)s',
                   {'name': name.upper()})
    rows = cursor.fetchall()
    numbers = []
    for row in rows:
        numbers.append(row['number'])

    cursor.execute('select number, name from name_variants where number=ANY(%(numbers)s)',
                   {'numbers': numbers})

    rows = cursor.fetchall()
    result = []

    for row in rows:
        result.append({
            'name': row['name'],
            'number': row['number']
        })
    return result