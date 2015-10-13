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
