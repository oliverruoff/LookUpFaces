"""
This script is for defragmenting the images within a
dropbox account. Meaning sorting them after their metadata.
"""
import os
from datetime import datetime as dt

import dropbox
from dotenv import load_dotenv

# loading .env file
load_dotenv()

FILE_NAME_ENDINGS_TO_FILTER_ON = ['jpg', 'jpeg', 'png', 'mp4', 'avi']
BLOCK_LIST = ['WA']
# List of folders where files will not be listed
LOOKUP_FOLDER_LIST = ['/Smartphone Sync']
# Path where files will be copied
RELOCATION_PATH = '/DefragBox'


def init_dropbox(dropbox_token: str):
    return dropbox.Dropbox(dropbox_token)


def list_files(dbx: dropbox.Dropbox, lookup_folder: list):
    all_folder_entries = []
    for folder in lookup_folder:
        response = dbx.files_list_folder(folder, recursive=True)
        entries = response.entries
        while response.has_more:
            print(dt.now(), 'Listing files... Found so far:', len(entries))
            response = dbx.files_list_folder_continue(response.cursor)
            entries += response.entries
        all_folder_entries += entries
    return all_folder_entries


def filter_files_on_name_ending(files: list, name_endings: list):
    return [_file for _file in files if any([_file.name.endswith(ending) for ending in name_endings])]


def filter_files_on_name_contains_any_from_block_list(files: list, block_list):
    return [_file for _file in files if not any([blocked_word in _file.name for blocked_word in block_list])]


def get_relocationpath_for_file(file_metadata, to_path_prefix=RELOCATION_PATH):

    year = str(file_metadata.client_modified.year)
    month = '0' + str(file_metadata.client_modified.month) if \
        len(str(file_metadata.client_modified.month)) == 1 else str(file_metadata.client_modified.month)
    day = '0' + str(file_metadata.client_modified.day) if \
        len(str(file_metadata.client_modified.day)) == 1 else str(file_metadata.client_modified.day)
    _new_file_name = day + '.' + month + '.' + year + '__' + file_metadata.name
    _to_path = '/'.join([to_path_prefix, year, month, day, _new_file_name])
    return dropbox.files.RelocationPath(from_path=file_metadata.path_lower, to_path=_to_path)


def batch_copy_chunks(dropbox_client: dropbox.Dropbox, relocation_paths: list, chunk_size: int = 1000):
    for i in range(0, len(relocation_paths), chunk_size):
        if i > len(relocation_paths)-chunk_size:
            print('Copying chunk:', i, '-', len(relocation_paths))
            dropbox_client.files_copy_batch_v2(relocation_paths[i:])
        else:
            print('Copying chunk:', i, '-', i+chunk_size)
            dropbox_client.files_copy_batch_v2(
                relocation_paths[i:i+chunk_size])


if __name__ == '__main__':
    dbx = init_dropbox(os.getenv('DROPBOX_TOKEN'))
    print(dt.now(), 'Loading all files. This will take a while (Depending on the amount of files in your dropbox).')
    unfiltered_files = list_files(dbx, LOOKUP_FOLDER_LIST)
    print(dt.now(), 'Found', len(unfiltered_files), 'files.')
    already_copied_file_names = [f.name.split(
        '__')[1] for f in list_files(dbx, [RELOCATION_PATH]) if '__' in f.name]
    print(dt.now(), 'Found', len(already_copied_file_names),
          'files, that were already copied.')
    prefiltered_files = [
        f for f in unfiltered_files if f.name not in (already_copied_file_names)]
    print(dt.now(), 'List now contains', len(prefiltered_files), 'files.')
    name_endings = FILE_NAME_ENDINGS_TO_FILTER_ON + \
        [ending.upper() for ending in FILE_NAME_ENDINGS_TO_FILTER_ON]
    print(dt.now(), 'Filtering files on endings:', name_endings)
    image_files = filter_files_on_name_ending(unfiltered_files, name_endings)
    print(dt.now(), 'Found', len(image_files), 'image files.')
    print(dt.now(), 'Filtering files on block list words:', BLOCK_LIST)
    image_files = filter_files_on_name_contains_any_from_block_list(
        image_files, BLOCK_LIST)
    print(dt.now(), 'Remaining files:', len(image_files))
    relocation_paths = [get_relocationpath_for_file(img_file) for
                        img_file in image_files if type(img_file) == dropbox.files.FileMetadata]
    sample = relocation_paths[0] if len(relocation_paths) > 0 else None
    print(dt.now(), 'Batch copying the files to sorted folders. 1st relocation path sample:', sample)
    upload_progress = 0
    for relocation_path in relocation_paths:
        upload_progress += 1
        print(dt.now(), 'Uploading:', relocation_path,
              '(', upload_progress, '/', len(relocation_paths), ')')
        try:
            dbx.files_copy_v2(relocation_path.from_path,
                              relocation_path.to_path)
        except dropbox.exceptions.ApiError as e:
            print(dt.now(), 'Error while copying file. Continuing...')
            print(e)
    print(dt.now(), 'Done!')
