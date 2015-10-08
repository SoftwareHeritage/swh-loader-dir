#!/usr/bin/env python3

# Tryouts scratch buffer
# Not for production

# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import shutil
import tempfile

from swh.loader.dir.git import git, utils


def write_file(root, file, content):
    """Write some content in a file.

    """
    filename = os.path.join(root, file)
    with open(filename, 'w') as f:
        f.write(content)


def mkdir(root, name):
    """Create a directory path on disk.

    """
    full_foldername = os.path.join(root, name)
    os.makedirs(full_foldername, exist_ok=True)
    return full_foldername


def git_ls_tree_rec(hashes, info):
    """Display the computed result for debug purposes.

    """
    for entry in hashes.keys():
        entry_properties = hashes[entry]
        print("entry name: %s" % entry)
        for file in entry_properties:
            sha1 = utils.hash_to_hex(file['sha1_git'])
            print("%s %s %s\t%s" % (file['perms'].value.decode('utf-8'),
                                    file['type'].value.decode('utf-8'),
                                    sha1,
                                    file['name'].decode('utf-8')))
        print()

    revision = git.compute_revision_git_sha1(hashes, info)
    print('revision %s -> directory %s' % (
        utils.hash_to_hex(revision['sha1_git']),
        utils.hash_to_hex(hashes['<root>'][0]['sha1_git'])
    ))


### setup - prepare some arborescence with dirs and files to walk it

tempfilename = tempfile.mktemp(prefix='swh.loader.dir', suffix='.tmp',
                               dir='/tmp')
# want the same name for idempotency
scratch_folder_root = mkdir(tempfilename, 'tmp')

mkdir(scratch_folder_root, 'empty-folder')
scratch_folder_foo = mkdir(scratch_folder_root, 'foo')
scratch_folder_bar = mkdir(scratch_folder_root, 'bar/barfoo')

write_file(scratch_folder_foo,
           'quotes.md',
           'Shoot for the moon. Even if you miss, you\'ll land among '
           'the stars.')

write_file(scratch_folder_bar,
           'another-quote.org',
           'A Victory without danger is a triumph without glory.\n'
           '-- Pierre Corneille')

ADDITIONAL_INFO = {
    'revision_author_name': 'swh author',
    'revision_author_email': 'swh@inria.fr',
    'revision_author_date': '1444054085',
    'revision_author_offset': '+0200',
    'revision_committer_name': 'swh committer',
    'revision_committer_email': 'swh@inria.fr',
    'revision_committer_date': '1444054085',
    'revision_committer_offset': '+0200',
    'revision_type': 'dir',
    'revision_message': 'synthetic revision message'
}

# when
hashes = git.walk_and_compute_sha1_from_directory(scratch_folder_root)

# then
git_ls_tree_rec(hashes, ADDITIONAL_INFO)

### teardown
shutil.rmtree(tempfilename, ignore_errors = True)
