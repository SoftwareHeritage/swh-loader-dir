#!/usr/bin/env python3

import os
import shutil
import tempfile

from swh.core import hashutil


def compute_hashes(dirpath, filename):
    """Given a fullname, compute its hashes.

    Args:
        dirpath: the absolute path of the filename
        filename: the file's name

    Returns:
        The computed hash for that filename.

    Assumes:
        The full computed path exists.

    """
    fullname = os.path.join(dirpath, filename)
    return hashutil.hashfile(fullname)


# echo <git ls-tree format input> | git mktree --missing

def compute_directory_hash(dirpath, hashes):
    """Compute a directory git sha1 for a dirpath.

    Args:
        dirpath: the absolute path of the directory
        hashes: list of dictionaries with keys:
            - sha1_git:
            - path: directory parent of the filename
            - name: file's name

        Returns:
            sha1 git of the directory

        Assumes:
            Every path exists.
    """
    def row_entry_tree_format(hashes):
        return map(lambda entry:
                   entry['perms'] + b' ' + entry['name'] + b'\0' +
                   entry['sha1_git'],
                   hashes)

    rows = list(row_entry_tree_format(hashes))
    return hashutil.hashdata(b''.join(rows),
                             algorithms=['sha1_tree_git'])


def walk_from(dir):
    for dirpath, dirnames, filenames in os.walk(dir, topdown=False):
        print('dirpath: %s\ndirnames: %s' % (dirpath, dirnames))
        dir_hashes = []
        for filename in filenames:
            fullname = os.path.join(dirpath, filename)
            print('filename: %s' % filename)
            hashes = compute_hashes(dirpath, fullname)
            hashes.update({
                'name': bytes(filename, 'utf-8'),
                'parent': dirpath,
                'perms': bytes('100644', 'utf-8'),
            })
            print('hashes: %s' % hashes)
            dir_hashes.append(hashes)

        tree_hash = compute_directory_hash(dirpath, dir_hashes)
        tree_hash.update({
            'name': dirpath,
            'type': 'tree'
        })
        print("directory sha1: %s" % tree_hash)
        print()


def write_file(file, content):
    with open(file, 'w') as f:
        f.write(content)

# prepare some arborescence with dirs and files to walk it
scratch_folder_root = tempfile.mktemp(prefix='swh.loader.dir', suffix='.tmp', dir='/tmp')
scratch_folder_foo = os.path.join(scratch_folder_root, 'foo')
os.makedirs(scratch_folder_foo, exist_ok=True)
scratch_folder_bar = os.path.join(scratch_folder_root, 'bar/barfoo')
os.makedirs(scratch_folder_bar, exist_ok=True)

scratch_file = os.path.join(scratch_folder_foo, 'quotes.md')
write_file(scratch_file,
           'Shoot for the moon. Even if you miss, you\'ll land among the stars.')

scratch_file2 = os.path.join(scratch_folder_bar, 'another-quote.org')
write_file(scratch_file2,
           'A Victory without danger is a triumph without glory.\n-- Pierre Corneille')

walk_from(scratch_folder_root)

# clean up
shutil.rmtree(scratch_folder_root, ignore_errors = True)
