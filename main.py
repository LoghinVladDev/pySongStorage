from db.database_manager import DatabaseManager
from sys import argv
from song_storage_utils import *

if __name__ == '__main__':
    # DatabaseManager.init_database(force_clear=True)

    command = ''
    for i in range(1, len(argv)):
        command += argv[i] + ' '

    try:
        if command.startswith(AddSong().command_text):
            id = AddSong().decode(command).execute()
            print(f'Added song with id = {id}')

        if command.startswith(ModifySong().command_text):
            ModifySong().decode(command).execute()
            print(f'Modified Song')

        if command.startswith(Search().command_text):
            results = Search().decode(command).execute()
            print('Results:  ')
            for result in results:
                print(f"\tEntry With ID : {result['ID']}")
                print(f"\tSong File : {result['File Name']}")
                print(f"\tSong Title : {result['Title']}")
                print(f"\tSong Artist : {result['Artist']}")
                print(f"\tSong Album : {result['Album']}")
                print(f"\tRelease Year : {result['Release Year']}")
                print(f"\tDuration : {result['Duration']}")
                print(f"\tTags :")
                for tag in result['Tags']:
                    for k in tag.keys():
                        print(f'\t\t{k} = {tag[k]}')
                print()

        if command.startswith(CreateSaveList().command_text):
            CreateSaveList().decode(command).execute()
            print('Created SaveList Archive "Savelist.zip"')

        if command.startswith(Play().command_text):
            Play().decode(command).execute()

        if command.startswith(DeleteSong().command_text):
            DeleteSong().decode(command).execute()
            print(f'Deleted Song')
    except ValueError as FormatInvalid:
        print(FormatInvalid)

# Add_song ./temp/01-megadeth-the_threat_is_real.flac --title = The Threat is Real --album = Dystopia --release-year = 2016 --artist = Megadeth --tag = codec:flac --tag = sample rate:44100Hz