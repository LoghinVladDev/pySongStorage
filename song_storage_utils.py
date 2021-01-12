import shutil
from db.database_manager import DatabaseManager


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
    __parameters = [
        ('--name', 'deletes a song by title', None),
        ('--artist', 'deletes songs by artist name', None),
        ('--album', 'deletes songs by album', None),
        ('--release-year', 'deletes songs by release year', None),
        ('--tag', 'deletes songs by tag value', None, None)
    ]

    @property
    def command_text(self):
        return 'Delete_song'

    @property
    def description(self):
        return 'Deletes a song from the manager storage'

    @property
    def param_types(self):
        return 'Optional (instead of ID)'

    @property
    def param_names(self):
        param_string = ''

        for p in DeleteSong.__parameters:
            param_string += f'\t\t{p[0]} - {p[1]}\n'

        return param_string


class ModifySong(Command):
    __parameters = [
        ('--title', 'sets the name metadata value to the value given', None),
        ('--artist', 'sets the artist metadata value to the value given', None),
        ('--album', 'sets the album metadata value to the value given', None),
        ('--release-year', 'sets the release year metadata value to the value given', None),
        ('--duration', 'sets the duration metadata value to the value given', None),
        ('--tag', 'adds a tag for the song', None, None)
    ]

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
        ('--release-year', '[=, >, <, >=, <=] searches by release year', None),
        ('--duration', '[=, >, <, >=, <=] searches by duration', None),
        ('--tag', '[=] searches by tag value', None, None),
    ]

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

            arg_label_value = arg.split('=')
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


class CreateSaveList(Command):
    __parameters = [
        ('--title', '[=] searches by title', None),
        ('--artist', '[=] searches by artist', None),
        ('--album', '[=] searches by album', None),
        ('--release-year', '[=, >, <, >=, <=] searches by release year', None),
        ('--duration', '[=, >, <, >=, <=] searches by duration', None),
        ('--tag', '[=] searches by tag value', None, None),
    ]

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
            ' --tag = codec:mp3 --tag = sample rate:44100Hz').execute())
        print(AddSong().decode(
            'Add_song ./temp/02-megadeth-dystopia.flac --title = Dystopia --album = Dystopia '
            '--release-year = 2016 '
            ' --tag = codec:flac --tag = sample rate:44100Hz').execute())
        print(AddSong().decode(
            'Add_song ./temp/10-megadeth-lying_in_state.flac --title = Lying in State --album = Dystopia '
            '--release-year = 2016 '
            ' --tag = codec:flac --tag = sample rate:44100Hz').execute())
        print(AddSong().decode(
            'Add_song ./temp/01-megadeth-the_threat_is_real.flac --title = The Threat is Real --album = Dystopia '
            '--release-year = 2016 '
            ' --tag = codec:flac --tag = sample rate:44100Hz').execute())
    except ValueError as e:
        print(e)

