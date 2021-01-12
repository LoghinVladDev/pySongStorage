import shutil
from db.database_manager import DatabaseManager
import os
import zipfile
from pygame import mixer
from time import sleep

def to_s(seconds_value: str):
    if seconds_value.isnumeric():
        return int(seconds_value)

    if 'm' in seconds_value:
        minutes = seconds_value.split('m')[0]
        seconds = seconds_value.split('m')[1]

        if 's' in seconds:
            seconds = int(seconds[:seconds.find('s')])

        return int(minutes) * 60 + int(seconds)
    raise ValueError('Invalid Format of Time')


def to_m_s(seconds: int):
    minutes = seconds // 60
    seconds = seconds % 60

    return str(minutes) + "m " + str(seconds) + "s"


class Command(object):
    __parameters: [tuple] = []

    def __init__(self):
        self.__file_name = None

    @property
    def command_text(self):
        return 'Command'

    @property
    def param_names(self):
        return '\t\tNone'

    def execute(self):
        pass

    @property
    def description(self):
        return ''

    @property
    def default_parameter(self):
        return 'ID'

    @property
    def result(self):
        return 'None'

    @property
    def param_types(self):
        return 'Additional'

    def decode(self, string: str):
        return self

    @property
    def usage(self):
        return f"{self.command_text} '{self.default_parameter}' - {self.description}\n" \
               f"\t{self.param_types} Parameters:\n{self.param_names}\n" \
               f"\tResult:\n\t\t{self.result}\n"

    def set_file_name(self, file_name):
        self.__file_name = file_name
        return self

    @property
    def file_name(self):
        return self.__file_name

    def debug(self):
        print('COMMAND PROPERTIES : ')
        print(f'\t{self.command_text}')
        print(f'\t{self.description}')
        print(f'\t{self.default_parameter}')
        print(f'\t{self.result}')
        print(f'\t{self.param_types}')
        print('COMMAND VALUES : ')
        print(f'\t{self.__file_name}')


class AddSong(Command):
    __parameters = [
        ('--title', 'sets the name metadata value to the value given', None),
        ('--artist', 'sets the artist metadata value to the value given', None),
        ('--album', 'sets the album metadata value to the value given', None),
        ('--release-year', 'sets the release year metadata value to the value given', None),
        ('--duration', 'sets the duration metadata value to the value given', None),
        ('--tag', 'adds a tag for the song', None, None)
    ]

    def __init__(self):
        Command.__init__(self)
        self.__file_path = ''
        self.__modified_params = None

    @property
    def command_text(self):
        return 'Add_song'

    @property
    def description(self):
        return 'Adds a song to the manager storage'

    @property
    def default_parameter(self):
        return 'Song file path'

    @property
    def result(self):
        return 'ID of the song that will be inserted, or existing song ID'

    def execute(self) -> int:
        rows = DatabaseManager.execute_prepared('SELECT ID FROM song WHERE file_name = %s', (self.file_name,))

        if rows:
            return rows[0][0]

        shutil.copy2(self.__file_path, './storage')
        query = 'INSERT INTO song (file_name'
        values = '(%s'
        prep_values = [self.file_name]

        for p in self.__modified_params:
            if p[0] == '--title':
                query += ', song_name'
                values += ', %s'
                prep_values.append(p[2])
            if p[0] == '--artist':
                query += ', artist_id'
                values += ', %s'
                prep_values.append(DatabaseManager.get_artist_id(p[2]))
            if p[0] == '--album':
                query += ', album_id'
                values += ', %s'
                prep_values.append(DatabaseManager.get_album_id(p[2]))
            if p[0] == '--release-year':
                query += ', release_year'
                values += ', %s'
                prep_values.append(p[2])
            if p[0] == '--duration':
                query += ', duration_sec'
                values += ', %s'
                prep_values.append(to_s(p[2]))

        query += ') VALUES ' + values + ')'
        DatabaseManager.execute_prepared(query, tuple(prep_values))

        song_id = self.execute()

        for p in self.__modified_params:
            if p[0] == '--tag':
                DatabaseManager.execute_prepared('INSERT INTO song_tag (song_id, tag_id, value) VALUES (%s, %s, %s)',
                                                 (song_id, DatabaseManager.get_tag_id(p[2]), p[3]))

        return song_id

    @property
    def param_names(self):
        param_string = ''

        for p in AddSong.__parameters:
            param_string += f'\t\t{p[0]} - {p[1]}\n'

        return param_string

    def decode(self, string: str):
        parts = string.split(' ', 2)

        if len(parts) < 3:
            raise ValueError(f'{self.command_text} : not enough parameters')

        if parts[0] != self.command_text:
            raise ValueError(f'{self.command_text} : command name invalid')

        try:
            open(parts[1], 'rb').close()
            self.__file_path = parts[1]
        except IOError:
            raise ValueError(f'{self.command_text} : file path invalid')

        self.set_file_name(parts[1].strip().split('/')[-1])

        args = parts[2].split("--")
        self.__modified_params = []
        for arg in args:
            if not arg:
                continue

            if '=' not in arg:
                raise ValueError(f'{self.command_text} : format invalid. Attribute must have = between label and value')

            arg_label_value = arg.split('=')
            label = arg_label_value[0].strip()
            value = arg_label_value[1].strip()

            for p in self.__parameters:
                if p[0].endswith(label):
                    self.__modified_params.append((p[0], p[1], value) if p[0] != '--tag'
                                                  else (p[0], p[1], value.split(':')[0].strip(),
                                                        value.split(':')[1].strip()))

        return self

    def debug(self):
        Command.debug(self)
        print('ADD SONG : ')
        print(f'\t{self.__file_path}')
        for p in self.__modified_params:
            print(f'\t{p[0]} : {p[2]}, {p[3] if p[0] == "--tag" else ""}')


class DeleteSong(Command):
    __parameters = []

    @property
    def command_text(self):
        return 'Delete_song'

    @property
    def description(self):
        return 'Deletes a song from the manager storage'

    @property
    def default_parameter(self):
        return 'ID'

    def __init__(self):
        Command.__init__(self)
        self.__id = 0

    def decode(self, string: str):
        parts = string.split(' ', 1)

        if len(parts) < 1:
            raise ValueError(f'{self.command_text} : not enough parameters')

        if parts[0] != self.command_text:
            raise ValueError(f'{self.command_text} : command name invalid')

        self.__id = int(parts[1])

        return self

    def execute(self):
        rows = DatabaseManager.execute_prepared('SELECT ID, file_name FROM song WHERE id = %s', (self.__id,))
        if not rows:
            raise ValueError(f'{self.command_text} : Not a valid ID')

        DatabaseManager.execute_prepared('DELETE FROM song WHERE id=%s', (self.__id,))
        os.remove('./storage/' + rows[0][1])


class ModifySong(Command):
    __parameters = [
        ('--title', 'sets the name metadata value to the value given', None),
        ('--artist', 'sets the artist metadata value to the value given', None),
        ('--album', 'sets the album metadata value to the value given', None),
        ('--release-year', 'sets the release year metadata value to the value given', None),
        ('--duration', 'sets the duration metadata value to the value given', None),
        ('--atag', 'adds a tag for the song', None, None),
        ('--rtag', 'adds a tag for the song', None, None),
        ('--mtag', 'adds a tag for the song', None, None),
    ]

    def __init__(self):
        Command.__init__(self)
        self.__id = 0

    @property
    def default_parameter(self):
        return 'ID'

    def decode(self, string: str):
        parts = string.split(' ', 2)

        if len(parts) < 3:
            raise ValueError(f'{self.command_text} : not enough parameters')

        if parts[0] != self.command_text:
            raise ValueError(f'{self.command_text} : command name invalid')

        self.__id = int(parts[1])

        args = parts[2].split("--")
        self.__modified_params = []
        for arg in args:
            if not arg:
                continue

            if '=' not in arg:
                raise ValueError(f'{self.command_text} : format invalid. Attribute must have = between label and value')

            arg_label_value = arg.split('=')
            label = arg_label_value[0].strip()
            value = arg_label_value[1].strip()

            for p in self.__parameters:
                if p[0].endswith(label):
                    self.__modified_params.append((p[0], p[1], value) if not p[0].endswith('tag')
                                                  else (p[0], p[1], value.split(':')[0].strip(),
                                                        value.split(':')[1].strip()))

        return self

    def execute(self) -> None:
        rows = DatabaseManager.execute_prepared('SELECT ID FROM song WHERE id = %s', (self.__id,))

        if not rows:
            raise ValueError(f'{self.command_text} : ID not valid')

        query = 'UPDATE song set '
        values = '('
        prep_values = []

        for p in self.__modified_params:
            if p[0] == '--title':
                query += 'song_name = %s, '
                prep_values.append(p[2])
            if p[0] == '--artist':
                query += 'artist_id = %s, '
                prep_values.append(DatabaseManager.get_artist_id(p[2]))
            if p[0] == '--album':
                query += 'album_id = %s, '
                prep_values.append(DatabaseManager.get_album_id(p[2]))
            if p[0] == '--release-year':
                query += 'release_year = %s, '
                prep_values.append(p[2])
            if p[0] == '--duration':
                query += 'duration_sec = %s, '
                prep_values.append(to_s(p[2]))

        query = query.removesuffix(', ')
        query += " WHERE ID = %s"
        prep_values.append(self.__id)

        DatabaseManager.execute_prepared(query, tuple(prep_values))

        for p in self.__modified_params:
            if p[0] == '--atag':
                DatabaseManager.execute_prepared('INSERT INTO song_tag (song_id, tag_id, value) VALUES (%s, %s, %s)',
                                                 (self.__id, DatabaseManager.get_tag_id(p[2]), p[3]))

        # song_id = self.execute()

        # for p in self.__modified_params:
        #     if p[0] == '--tag':
        #         DatabaseManager.execute_prepared('INSERT INTO song_tag (song_id, tag_id, value) VALUES (%s, %s, %s)',
        #                                          (song_id, DatabaseManager.get_tag_id(p[2]), p[3]))

    @property
    def command_text(self):
        return 'Modify_data'

    @property
    def description(self):
        return 'Modifies a song from the manager storage'

    @property
    def param_names(self):
        param_string = ''

        for p in ModifySong.__parameters:
            param_string += f'\t\t{p[0]} - {p[1]}\n'

        return param_string


class Search(Command):
    __parameters = [
        ('--title', '[=] searches by title', None),
        ('--artist', '[=] searches by artist', None),
        ('--album', '[=] searches by album', None),
        ('--release-year', '[=] searches by release year', None),
        ('--tag', '[=] searches by tag value', None, None),
    ]

    def execute(self):
        rows = DatabaseManager.execute(
            'SELECT song.id, file_name, song_name, artist_id, album_id, song.release_year,'
            'duration_sec FROM song')

        for p in self.__modified_params:
            if p[0] == '--artist':
                artist_id = DatabaseManager.get_artist_id(p[2])
                rows = list(filter(lambda x: x[3] == artist_id, rows))
            if p[0] == '--album':
                album_id = DatabaseManager.get_album_id(p[2])
                rows = list(filter(lambda x: x[4] == album_id, rows))
            if p[0] == '--title':
                rows = list(filter(lambda x: x[2] == p[2], rows))
            if p[0] == '--release-year':
                rows = list(filter(lambda x: x[5] == int(p[2]), rows))

        for p in self.__modified_params:
            if p[0] == '--tag':
                tag_id = DatabaseManager.get_tag_id(p[2])
                tag_rows = list(filter(lambda x: x[2] == p[3], DatabaseManager.execute_prepared(
                    'SELECT song_id, tag_id, value FROM song_tag WHERE tag_id = %s', (tag_id,))))

                rows = list(filter(lambda x: x[0] in [song_id[0] for song_id in tag_rows], rows))

        return [{"ID": row[0], "File Name": row[1], "Title": row[2] if row[2] else "Unknown",
                 "Artist": DatabaseManager.get_artist_by_id(row[3]),
                 "Album": DatabaseManager.get_album_by_id(row[4]),
                 "Release Year": row[5]
                 if row[5] else "Unknown",
                 "Duration": to_m_s(row[6]) if row[6] else "Unknown",
                 "Tags": DatabaseManager.get_tags_for_song_id(row[0])} for row in rows]

    def __init__(self):
        Command.__init__(self)
        self.__modified_params = None

    def decode(self, string: str):
        parts = string.split(' ', 1)

        if len(parts) < 1:
            raise ValueError(f'{self.command_text} : not enough parameters')

        if parts[0] != self.command_text:
            raise ValueError(f'{self.command_text} : command name invalid')

        if len(parts) > 1:
            args = parts[1].split("--")
            self.__modified_params = []
            for arg in args:
                if not arg:
                    continue

                if '=' not in arg:
                    raise ValueError(
                        f'{self.command_text} : format invalid. Attribute must have = between label and value')

                arg_label_value = arg.split('=')
                # arg_label_value = re.split(r'=|>|<|>=|<=', arg)
                label = arg_label_value[0].strip()
                value = arg_label_value[1].strip()

                for p in self.__parameters:
                    if p[0].endswith(label):
                        self.__modified_params.append((p[0], p[1], value) if p[0] != '--tag'
                                                      else (p[0], p[1], value.split(':')[0].strip(),
                                                            value.split(':')[1].strip()))

        return self

    @property
    def command_text(self):
        return 'Search'

    @property
    def description(self):
        return 'Searches for song entries that match given filter'

    @property
    def param_names(self):
        param_string = ''

        for p in Search.__parameters:
            param_string += f'\t\t{p[0]} - {p[1]}\n'

        return param_string

    def debug(self):
        Command.debug(self)
        print('Search : ')
        for p in self.__modified_params:
            print(f'\t{p[0]} : {p[2]}, {p[3] if p[0] == "--tag" else ""}')


class CreateSaveList(Command):
    __parameters = [
        ('--title', '[=] searches by title', None),
        ('--artist', '[=] searches by artist', None),
        ('--album', '[=] searches by album', None),
        ('--release-year', '[=, >, <, >=, <=] searches by release year', None),
        ('--duration', '[=, >, <, >=, <=] searches by duration', None),
        ('--tag', '[=] searches by tag value', None, None),
    ]

    def __init__(self):
        Command.__init__(self)
        self.__entries = []

    def execute(self):
        os.mkdir('./.zip')
        paths = ['./storage/' + entry['File Name'] for entry in self.__entries]

        for path in paths:
            shutil.copy2(path, './.zip')

        shutil.make_archive('Savelist', 'zip', './.zip')

        for entry in self.__entries:
            os.remove('./.zip/' + entry['File Name'])
        os.rmdir('./.zip')

    def decode(self, string: str):
        self.__entries = Search().decode(Search().command_text + string.removeprefix(self.command_text)).execute()
        return self

    @property
    def command_text(self):
        return 'Create_save_list'

    @property
    def description(self):
        return 'Saves and archives songs that match given filter'

    @property
    def param_names(self):
        param_string = ''

        for p in CreateSaveList.__parameters:
            param_string += f'\t\t{p[0]} - {p[1]}\n'

        return param_string


class Play(Command):
    @property
    def command_text(self):
        return 'Play'

    @property
    def description(self):
        return 'Plays song given'

    @property
    def default_parameter(self):
        return 'ID'

    def __init__(self):
        Command.__init__(self)
        self.__id = 0

    def decode(self, string: str):
        parts = string.split(' ', 1)

        if len(parts) < 1:
            raise ValueError(f'{self.command_text} : not enough parameters')

        if parts[0] != self.command_text:
            raise ValueError(f'{self.command_text} : command name invalid')

        self.__id = int(parts[1])

        return self

    def execute(self):
        rows = DatabaseManager.execute_prepared('SELECT ID, file_name, song_name, artist_id,'
                                                'duration_sec FROM song WHERE id = %s', (self.__id,))
        if not rows:
            raise ValueError(f'{self.command_text} : Not a valid ID')

        print(f'Playing {rows[0][2]} by {DatabaseManager.get_artist_by_id(rows[0][3])}. '
              f'Duration : {to_m_s(rows[0][4]) if rows[0][4] else "Unknown. Playing first 10 seconds"}...')

        mixer.init()
        mixer.music.load('./storage/' + rows[0][1])
        mixer.music.play()

        sleep(rows[0][4] if rows[0][4] else 10)


if __name__ == '__main__':
    DatabaseManager.init_database(force_clear=True)
    # print(AddSong().usage)
    # print(DeleteSong().usage)
    # print(ModifySong().usage)
    # print(Search().usage)
    # print(CreateSaveList().usage)
    # print(Play().usage)

    try:
        print(AddSong().decode(
            'Add_song ./temp/Rust_In_Peace_Polaris.mp3 --title = Rust In Peace Polaris --album = Rust In Peace '
            '--release-year = 1990 '
            '--artist = Megadeth '
            ' --tag = codec:mp3 --tag = sample rate:44100Hz').execute())
        print(AddSong().decode(
            'Add_song ./temp/02-megadeth-dystopia.flac --title = Dystopia --album = Dystopia '
            '--artist = Megadeth '
            '--release-year = 2016 '
            ' --tag = codec:flac --tag = sample rate:44100Hz').execute())
        print(AddSong().decode(
            'Add_song ./temp/10-megadeth-lying_in_state.flac --title = Lying in State --album = Dystopia '
            '--release-year = 2016 '
            ' --tag = codec:flac --tag = sample rate:44100Hz').execute())
        print(AddSong().decode(
            'Add_song ./temp/01-megadeth-the_threat_is_real.flac --title = The Threat is Real --album = Dystopia '
            '--release-year = 2016 '
            '--artist = Megadeth '
            ' --tag = codec:flac --tag = sample rate:44100Hz').execute())

        print(Search().decode('Search --tag = codec:flac').execute())
        print(Search().decode('Search ').execute())

        print(DeleteSong().decode('Delete_song 3').execute())

        print(Search().decode('Search ').execute())

        print(ModifySong().decode('Modify_data 2 --title = Tornado of Souls --album = Rust in Peace '
                                  '--release-year = 1990 --duration = 5m 30s --atag = channels:stereo').execute())

        print(Search().decode('Search ').execute())

        print(CreateSaveList().decode('Create_save_list --album = Rust in Peace').execute())

        print(Play().decode('Play 2').execute())
    except ValueError as e:
        print(e)
