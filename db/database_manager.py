import mysql.connector
import json


class DatabaseManager(object):
    default_credentials_file_path = 'db/cred.json'

    __instance = None

    def __init__(self, credentials_file_path: str = default_credentials_file_path):
        self.__conn: mysql.connector.connection.MySQLConnection = None

        try:
            credentials = json.load(open(credentials_file_path))
            self.connect(
                host=credentials['host'],
                username=credentials['user'],
                password=credentials['pass'],
                db=credentials['db']
            )
        except IOError as ConfigFilePathError:
            print('Configuration File Path Given / Default Config File does not point to a valid file')

    def connect(self, username, password, host='localhost', db='song_storage'):
        self.__conn = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=db
        )

        return self

    def execute_statement(self, statement: str, params: [] = None) -> [tuple]:
        if self.__conn is None:
            raise ConnectionError('Database Connection was not created')

        cursor: mysql.connector.connection.MySQLCursor = self.__conn.cursor(prepared=params is not None)
        cursor.execute(statement, params)

        if statement.lower().startswith('select') or statement.lower().startswith('update') or \
                statement.lower().startswith('delete') or statement.lower().startswith('insert'):
            result_set: [] = cursor.fetchall()
        else:
            result_set = []

        cursor.close()

        self.__conn.commit()

        return result_set if result_set else []

    @staticmethod
    def execute(statement: str) -> []:
        conn = DatabaseManager()

        return conn.execute_statement(statement)

    @staticmethod
    def execute_prepared(statement: str, params: [] = None) -> [tuple]:
        conn = DatabaseManager()

        return conn.execute_statement(statement, params)

    @staticmethod
    def init_database(script_path: str = 'db/init_script.sql', force_clear: bool = False, pass_cnt: int = 3):
        try:
            with open(script_path, 'r') as script_file:
                remainder: str = ''
                statements: [str] = []
                current_statement: str = ''

                for line in script_file.readlines():
                    if ';' in line:
                        statements.append(current_statement + line.split(';')[0])
                        current_statement = line.split(';', 2)[1]
                    else:
                        current_statement += line

                if current_statement.strip():
                    statements.append(current_statement)

                tables = [entry[0].lower() for entry in DatabaseManager.execute('SELECT table_name FROM '
                                                                                'information_schema.tables')]

                if force_clear:
                    for p in range(pass_cnt):
                        for s in statements:
                            if not s.strip().lower().startswith('create table'):
                                continue

                            table_name: str = s[s.find('table ') + len('table '):s.find('(') - 1]

                            if table_name.lower() in tables:
                                try:
                                    DatabaseManager.execute(f'DROP TABLE {table_name}')
                                    tables.remove(table_name.lower())
                                except Exception as Ignored:
                                    pass

                for s in statements:
                    if not s.strip().lower().startswith('create table'):
                        DatabaseManager.execute(s)
                        continue

                    table_name: str = s[s.find('table ') + len('table '):s.find('(') - 1]

                    if table_name.lower() not in tables:
                        DatabaseManager.execute(s)
                        print(f'Table {table_name} did not exist. Created now.')

        except IOError as PathInvalid:
            print('Path Given is Invalid')

    @staticmethod
    def get_artist_id(artist_name: str):
        rows = DatabaseManager.execute_prepared('SELECT ID FROM artist WHERE name = %s', (artist_name, ))
        if rows:
            return rows[0][0]

        DatabaseManager.execute_prepared('INSERT INTO artist (name) VALUES (%s)', (artist_name, ))
        DatabaseManager.get_artist_id(artist_name)

    @staticmethod
    def get_album_id(album_name: str):
        rows = DatabaseManager.execute_prepared('SELECT ID FROM album WHERE name = %s', (album_name, ))
        if rows:
            return rows[0][0]

        DatabaseManager.execute_prepared('INSERT INTO album (name) VALUES (%s)', (album_name, ))
        DatabaseManager.get_album_id(album_name)
