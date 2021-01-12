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

        cursor: mysql.connector.connection.MySQLCursor = self.__conn.cursor()
        cursor.execute(statement, params)

        if statement.lower().startswith('select') or statement.lower().startswith('update') or \
                statement.lower().startswith('delete') or statement.lower().startswith('insert'):
            result_set: [] = cursor.fetchall()
        else:
            result_set = []

        cursor.close()

        self.__conn.commit()

        return result_set if result_set else [tuple]

    @staticmethod
    def execute(statement: str, params: [] = None) -> [tuple]:
        conn = DatabaseManager()

        return conn.execute_statement(statement, params)

    @staticmethod
    def init_database(script_path: str = 'db/init_script.sql'):
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

                for s in statements:
                    table_name: str = s[s.find('table ') + len('table '):s.find('(') - 1]

                    if table_name.lower() not in tables:
                        DatabaseManager.execute(s)
                        print(f'Table {table_name} did not exist. Created now.')

        except IOError as PathInvalid:
            print('Path Given is Invalid')
