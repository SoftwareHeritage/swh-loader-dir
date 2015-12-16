#!/usr/bin/env python3

import os
import subprocess

from swh.model.hashutil import hash_path, hash_to_bytes

BATCH_SIZE = 10000


config = {
    # with git data for listing trees
    'dir_path_git': '/home/tony/work/inria/repo/linux-tryouts-git',

    # without anything git related
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
    hashes = hash_path(filepath)
    hashes.update({'length': os.path.getsize(filepath)})
    return hashes


def check_missing_contents(rootpath):
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
        if count_batch_contents < BATCH_SIZE:  # accumulate content to check
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
    print()


def git_ls_tree(rootpath):
    """Git ls tree from rootpath's latest revision's tree.

    Yields:
        Tuple of (perms, type, hex sha1, name)

    """
    with subprocess.Popen(
            ['git', 'ls-tree', '-r', '-t', 'master^{tree}'],
            stdout=subprocess.PIPE,
            cwd=rootpath) as proc:
        for line in proc.stdout:
            yield line.strip().decode('utf-8').replace('\t', ' ').split(' ')


def trees(rootpath):
    """Filter tree from rootpath in swh's api compliant with search.

    Yields:
        SWH compliant directory structure.

    """
    for _, type, hex_sha1, name in git_ls_tree(rootpath):
        if type == 'tree':
            yield{'id': hash_to_bytes(hex_sha1),
                  'name': name}


def check_missing_trees(rootpath):
    print('Folder to check: %s' % rootpath)
    # List of dirs to check in storage
    dirs_batch = []
    # map of dir index by sha1, value is their actual path
    dirs_map = {}
    # full dirs missing is a list of files not in storage
    dir_missings = []
    # batch of dirs to check
    count_batch_dirs = 0
    # total number of checked dirs
    count_checked_dirs = 0
    # nb trees read
    nb_dirs = 0

    for tree in trees(rootpath):
        nb_dirs += 1
        tree_id = tree['id']
        dirs_map.update({tree_id: tree['name']})
        dirs_batch.append(tree_id)
        count_batch_dirs += 1
        if count_batch_dirs < BATCH_SIZE:  # accumulate dir to check on storage
            continue

        print('Checks %s dirs' % len(dirs_batch))
        for dir_missing in storage.directory_missing(dirs_batch):
            dir_missings.append(dirs_map[dir_missing['id']])
        count_checked_dirs += count_batch_dirs

        # reinitialize list
        dirs_batch = []
        count_batch_dirs = 0

    if dirs_batch is not []:
        dirs_batch_len = len(dirs_batch)
        print('Checks %s dirs' % dirs_batch_len)
        for dir_missing in storage.directory_missing(dirs_batch):
            dir_missings.append(dirs_map[dir_missing['sha1']])
        count_checked_dirs += dirs_batch_len

    print('Number of dirs checked: %s' % count_checked_dirs)
    print('Number of dirs: %s' % nb_dirs)
    print('Stats on missing dirs -')
    if len(dir_missings) > 0:
        print('Missing files: ')
        for file_missing in dir_missings:
            print('- %s', file_missing)
    else:
        print('Nothing missing!')
    print()


check_missing_contents(config['dir_path'])
check_missing_trees(config['dir_path_git'])
