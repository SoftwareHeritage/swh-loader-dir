#!/usr/bin/env python3

import os
import subprocess

from swh.loader.dir.git import utils


BATCH_SIZE=10000


config = {
    'dir_path': '/home/tony/work/inria/repo/linux-tryouts',

    'storage_class': 'remote_storage',
    'storage_args': ['http://localhost:5000/'],
}


if config['storage_class'] == 'remote_storage':
    from swh.storage.api.client import RemoteStorage as Storage
else:
    from swh.storage import Storage


storage = Storage(*config['storage_args'])


def list_files_from(rootpath):
    """Git ls tree from rootpath's latest revision's tree.

    Yields:
        Tuple of (perms, type, hex sha1, name)

    """
    with subprocess.Popen(
            ['find', '.', '-type', 'f'],
            stdout=subprocess.PIPE,
            cwd=rootpath) as proc:
        for filepath in proc.stdout:
            yield os.path.join(rootpath, filepath.strip().decode('utf-8'))


def hashfile(filepath):
    """Hash a file according to what expects storage's api.

    """
    hashes = utils.hashfile(filepath)
    hashes.update({'length': os.path.getsize(filepath)})
    return hashes


def check_missing_content_from_file(rootpath):
    print('Folder to check: %s' % rootpath)
    # List of contents to check in storage
    contents_batch = []
    # map of content index by sha1, value is their actual path
    contents_map = {}
    # full contents missing is a list of files not in storage
    content_missings = []
    # batch of contents to check
    count_batch_contents = 0
    # total number of checked contents
    count_checked_contents = 0
    # nb files read
    nb_files = 0

    for filepath in list_files_from(rootpath):
        nb_files += 1
        content_hashes = hashfile(filepath)
        contents_map.update({content_hashes['sha1']: filepath})
        contents_batch.append(content_hashes)
        count_batch_contents += 1
        if count_batch_contents < BATCH_SIZE:  # accumulate content to check on storage
            continue

        print('Checks %s contents' % len(contents_batch))
        for content_missing in storage.content_missing(contents_batch):
            content_missings.append(contents_map[content_missing['sha1']])
        count_checked_contents += count_batch_contents

        # reinitialize list
        contents_batch = []
        count_batch_contents = 0

    if contents_batch is not []:
        contents_batch_len = len(contents_batch)
        print('Checks %s contents' % contents_batch_len)
        for content_missing in storage.content_missing(contents_batch):
            content_missings.append(contents_map[content_missing['sha1']])
        count_checked_contents += contents_batch_len

    print('Number of contents checked: %s' % count_checked_contents)
    print('Number of files: %s' % nb_files)
    print('Stats on missing contents -')
    if len(content_missings) > 0:
        print('Missing files: ')
        for file_missing in content_missings:
            print('- %s', file_missing)
    else:
        print('Nothing missing!')

check_missing_content_from_file(config['dir_path'])
