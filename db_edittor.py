import sqlite3

DB_NAME = 'offer_recommender.db'

class TableAlreadyExistsError(Exception):
    pass

class Character:
    TABLE_NAME = 'character'
    FIELDS = (
        ('name', 'text primary key'),
        ('display_name', 'text'),
        ('rarity', 'integer'),
        ('belongs', 'integer'),
        ('priority', 'integer')
    )

    def __init__(self, name, display_name, rarity, belongs=False, priority=0):
        self.name = name
        self.display_name = display_name
        self.rarity = rarity
        self.belongs = belongs
        self.priority = priority

    def make_values_tuple(self):
        return (self.name, self.display_name, self.rarity, self.belongs, self.priority)

class Term:
    TABLE_NAME = 'term'
    FIELDS = (
        ('name', 'text primary key'),
        ('display_name', 'text'),
        ('priority', 'integer')
    )

    def __init__(self, name, display_name, priority=0):
        self.name = name
        self.display_name = display_name
        self.priority = priority
        
    def make_values_tuple(self):
        return (self.name, self.display_name, self.priority)

class Junction:
    TABLE_NAME = 'junction'
    FIELDS = (
        ('term_name', 'integer'),
        ('character_name', 'integer'),
        ('foreign key(term_name)', 'references term(name)'),
        ('foreign key(character_name)', 'references character(name)')
    )

    def __init__(self, term_name, character_name):
        self.term_name = term_name
        self.character_name = character_name
        
    def make_values_tuple(self):
        return (self.term_name, self.character_name)

def query_create(table_name, fields):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()
    print(table_name)

    cursor.execute('select count(*) from sqlite_master where type="table" and name=?', (table_name,))
    res = cursor.fetchone()
    print(res)

    if res[0] == 0:
        try:
            query = 'create table {} ('.format(table_name)
            for f in fields:
                query += '{} {},'.format(f[0], f[1])
            query = query[:-1]
            query += ');'

            fields_unpacked = []
            for f in fields:
                fields_unpacked.append(f[0])
                fields_unpacked.append(f[1])

            cursor.execute(query)

            print('Created table "{}".'.format(table_name))
        except Exception as e:
            print('failed to create table.')
            print(e)
    else:
        raise TableAlreadyExistsError('Table "{}" already exists.'.format(table_name))

    connection.close()

def create_table():
    print('which table do you want to create?')
    print('[character, term, junction]')
    table_name = input('>> ')

    try:
        if table_name == 'character':
            query_create(
                Character.TABLE_NAME,
                Character.FIELDS
            )
        elif table_name == 'term':
            query_create(
                Term.TABLE_NAME,
                Term.FIELDS
            )
        elif table_name == 'junction':
            query_create(
                Junction.TABLE_NAME,
                Junction.FIELDS
            )
        else:
            print('canceled.\n')
            return
    except Exception as e:
        print('The table was not created.')
        print(e)

    print('')

def input_data(TableMaker):
    print('** Required data **')
    for f in TableMaker.FIELDS:
        print('{}: {}'.format(f[0], f[1]))
    print('\nSuccessively input above data separated with space.')
    print('Type "e" to end.')

    dataToInsert = []

    query = 'insert into {} values'.format(TableMaker.TABLE_NAME)

    while True:
        try:
            data = input('... ')
            if data == 'e':
                break
            print(data.split(' '))
            tm = TableMaker(*data.split(' '))

            values = tm.make_values_tuple()
        except Exception as e:
            print("couldn't add data.")
            print(e)
        else:
            query += '('
            query += ('?, ' * len(values))[:-2]
            query += '),'

            dataToInsert.extend(values)

    query = query[:-1]
    if len(dataToInsert) > 0:
        try:
            connection = sqlite3.connect(DB_NAME)
            connection.execute('pragma foreign_keys = 1')

            cursor = connection.cursor()
            print(query)
            print(dataToInsert)
            cursor.execute(query, tuple(dataToInsert))

            connection.commit()
            connection.close()
        except Exception as e:
            print('failed to insert.')
            print(e)
        else:
            print('successfully added data.')
        finally:
            connection.close()
    else:
        print('no data was added.')

def add_data():
    print('which table do you want to add data to?')
    print('[character, term, junction]')
    table_name = input('>> ')

    if table_name == 'character':
        input_data(Character)
    elif table_name == 'term':
        input_data(Term)
    elif table_name == 'junction':
        input_data(Junction)
    else:
        print('canceled.\n')
        return
    
    print('')

def select_file(TableMaker):
    print('not implemented.')
    pass

def add_data_from_file():
    print('which table do you want to add data to?')
    print('[character, term, junction]')
    table_name = input('>> ')

    if table_name == 'character':
        select_file(Character)
    elif table_name == 'term':
        select_file(Term)
    elif table_name == 'junction':
        select_file(Junction)
    else:
        print('canceled.\n')
        return
    
    print('')

def query_update(TableMaker, cursor, value_pair, where, where_bound_tuple):

    query = 'update {} set '.format(TableMaker.TABLE_NAME)
    query += '{} = ? '.format(value_pair[0])
    query += where

    print(query)
    print((value_pair[1], *where_bound_tuple))
    cursor.execute(query, (value_pair[1], *where_bound_tuple))

def update_row_by_name(TableMaker):
    connection = sqlite3.connect(DB_NAME)
    connection.execute('pragma foreign_keys = 1')
    cursor = connection.cursor()

    while True:
        print('input the name of the row that you want to change.')
        print('input "e" to end.')
        name = input('name... ')
        if name == 'e':
            break

        print('selectable columns:')
        for f in TableMaker.FIELDS:
            print('{}: {}'.format(f[0], f[1]))
        
        print('\ninput column to change and value separated by space.')
        print('input "e" to end.')

        change = input('...')

        if change == 'e':
            break
        
        update_pair = change.split(' ')

        if len(update_pair) == 2:
            try:
                query_update(TableMaker, cursor, update_pair, 'where name=?', (name, ))
            except Exception as e:
                print('failed to update.')
                print(e)
            else:
                print('successfully changed the data.')
            
    connection.commit()
    connection.close()

# TableMaker = Junction in this function
def update_row_by_pair(TableMaker):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    while True:
        print("input character's name and term's name separated space, in this order")
        print('input "e" to end.')
        names = input('name pair... ')
        if names == 'e':
            break
        name_pair = names.split(' ')

        print('selectable columns:')
        for f in TableMaker.FIELDS:
            print('{}: {}'.format(f[0], f[1]))

        print('input column to change and value separated by space.')
        print('input "e" to end.')

        change = input('...')

        if change == 'e':
            break
        
        update_pair = change.split(' ')

        if len(name_pair) == 2 and len(update_pair) == 2:
            try:
                query_update(TableMaker, cursor, update_pair, 'where character_name=? and term_name=?', tuple(name_pair))
            except Exception as e:
                print('failed to update.')
                print(e)

    connection.commit()
    connection.close()


def update_data():
    print('which table do you want update?')
    print('[character, term, junction]')
    table_name = input('>> ')

    if table_name == 'character':
        update_row_by_name(Character)
    elif table_name == 'term':
        update_row_by_name(Term)
    elif table_name == 'junction':
        update_row_by_pair(Junction)
    
    print('')

def show_query(table_name, display_name=None):
    connection = sqlite3.connect(DB_NAME)

    query = 'select * from {}'.format(table_name)
    cursor = connection.cursor()
    if display_name:
        query += ' where display_name == ?'
        cursor.execute(query, (display_name,))
    else:
        cursor.execute(query)
    res = cursor.fetchall()

    connection.close()

    return res

def show_table():
    print('about created table...')
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM sqlite_master WHERE TYPE="table"')
    res = cursor.fetchall()
    print(res)
    print('')
    connection.close()

    print('which table do you want to see?')
    print('[character, term, junction]')
    table_name = input('>> ')

    try:
        if table_name == 'character' or table_name == 'term' or table_name == 'junction':
            res = show_query(table_name)

            if len(res) > 0:
                for r in res:
                    print(r)
            else:
                print('No rows are registered.')

        else:
            print('canceled.\n')
            return
    except Exception as e:
        print('Failed to select rows from the table.')
        print(e)

    input('confirm...')
    print('')

def show_row_by_name():
    print('which table do you want to see?')
    print('[character, term]')
    table_name = input('>> ')

    try:
        if table_name == 'character' or table_name == 'term':
            print('what DISPLAY name do you want to see?')
            display_name = input('>> ')
            res = show_query(table_name, display_name)

            if len(res) > 0:
                for r in res:
                    print(r)
            else:
                print('No such rows are registered.')

        else:
            print('canceled.\n')
            return
    except Exception as e:
        print('Failed to select rows from the table.')
        print(e)
    
    
command = '\0'

while command != 'e':
    print('c: create table')
    print('a: add data to a table')
    print('af: add data from file')
    print('u: update data')
    print('s: show table')
    print('sn: show a row with the given name')
    print('e: exit')

    command = input('>> ')

    if command == 'c':
        create_table()
    elif command == 'a':
        add_data()
    elif command == 'af':
        add_data_from_file()
    elif command == 'u':
        update_data()
    elif command == 's':
        show_table()
    elif command == 'sn':
        show_row_by_name()

