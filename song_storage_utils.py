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

    @property
    def usage(self):
        return f"{self.command_text} '{self.default_parameter}' - {self.description}\n" \
               f"\t{self.param_types} Parameters:\n{self.param_names}\n" \
               f"\tResult:\n\t\t{self.result}\n"

    def set_file_name(self, file_name):
        self.__file_name = file_name
        return self


class AddSong(Command):

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

    def execute(self):
        pass


class DeleteSong(Command):
    __parameters = [
        ('--name', None, 'deletes a song by title'),
        ('--artist', None, 'deletes a song by artist name'),
        ('--tag', None, 'deletes a song by tag')
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
            param_string += f'\t\t{p[0]} - {p[2]}\n'

        return param_string


class ModifySong(Command):
    __parameters = [
        ('--name', None, 'modifies ')
    ]

    @property
    def command_text(self):
        return 'Modify_data'

    @property
    def description(self):
        return 'Modifies a song from the manager storage'


class Search(Command):
    @property
    def command_text(self):
        return 'Search'

    @property
    def description(self):
        return 'Searches for song entries that match given filter'


class CreateSaveList(Command):
    @property
    def command_text(self):
        return 'Create_save_list'

    @property
    def description(self):
        return 'Saves and archives songs that match given filter'


class Play(Command):
    @property
    def command_text(self):
        return 'Play'

    @property
    def description(self):
        return 'Plays song given'


if __name__ == '__main__':
    print(AddSong().usage)
    print(DeleteSong().usage)
    print(ModifySong().usage)
    print(Search().usage)
    print(CreateSaveList().usage)
    print(Play().usage)
