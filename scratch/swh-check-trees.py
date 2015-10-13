#!/usr/bin/env python3

import subprocess

from swh.core import hashutil


BATCH_SIZE = 1000

config = {
    'dir_path': '/home/tony/work/inria/repo/linux-tryouts-git',

    'storage_class': 'remote_storage',
    'storage_args': ['http://localhost:5000/'],
}


if config['storage_class'] == 'remote_storage':
    from swh.storage.api.client import RemoteStorage as Storage
else:
    from swh.storage import Storage


storage = Storage(*config['storage_args'])


def git_ls_tree(rootpath):
    """Git ls tree from rootpath's latest revision's tree.

    Yields:
        Tuple of (perms, type, hex sha1, name)

    """
    with subprocess.Popen(
            ['git', 'ls-tree', '-r', '-t', 'master^{tree}'],
            stdout=subprocess.PIPE,
            cwd=root_path) as proc:
        for line in proc.stdout:
            yield line.strip().decode('utf-8').replace('\t', ' ').split(' ')

def trees(rootpath):
    """Filter tree from rootpath in swh's api compliant with search.

    Yields:
        SWH compliant directory structure.

    """
    for _, type, hex_sha1, name in git_ls_tree(root_path):
        if type == 'tree':
            yield{'id': hashutil.hex_to_hash(hex_sha1),
                  'name': name}


def check_missing_trees(rootpath):
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


root_path = config['dir_path']
check_missing_trees(root_path)
