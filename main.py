from db.database_manager import DatabaseManager
from sys import argv

if __name__ == '__main__':
    DatabaseManager.init_database(force_clear=True)

    command = ''
    for i in range(1, len(argv)):
        command +=
