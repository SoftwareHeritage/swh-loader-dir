#!/usr/bin/env python3

import os
import shutil
import tempfile

from swh.core import hashutil
from swh.loader.dir import git
from swh.loader.dir.git import GitPerm, GitType


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


# Note: echo <git ls-tree format input> | git mktree --missing
def compute_directory_hash(dirpath, hashes):
    """Compute a directory git sha1 for a dirpath.

    Args:
        dirpath: the directory's absolute path
        hashes: list of tree entries with keys:
            - sha1_git: its sha1
            - name: file or subdir's name
            - perms: the tree entry's sha1 permissions
            - type: not used

        Returns:
            sha1 git of the directory

        Assumes:
            Every path exists.

    """
    def sort_by_entry_name(hashes):
        return sorted(hashes, key=lambda entry: entry['name'])

    def row_entry_tree_format(hashes):
        return map(lambda entry:
                   b''.join([entry['perms'].value,
                             b' ',
                             entry['name'],
                             b'\0',
                             entry['sha1_git']]),
                   hashes)

    rows = row_entry_tree_format(sort_by_entry_name(hashes[dirpath]))
    return git.hashdata(b''.join(rows), 'tree')

def walk_and_compute_sha1_from_directory(dir):
    """Compute git sha1 from directory dir.

    """
    ls_hashes = {}

    for dirpath, dirnames, filenames in os.walk(dir, topdown=False):
        hashes = []
        # FIXME: deal with empty directories which must be skipped!
        #  -> pb with bottom up approach

        # compute content hashes
        for filename in filenames:
            m_hashes = compute_hashes(dirpath, filename)
            m_hashes.update({
                'name': bytes(filename, 'utf-8'),
                'perms': GitPerm.file,  # FIXME symlink, exec file, gitlink...
                'type': GitType.file,
            })
            hashes.append(m_hashes)

        ls_hashes.update({
            dirpath: hashes
        })

        dir_hashes = []
        # compute directory hashes
        for dirname in dirnames:
            fullname = os.path.join(dirpath, dirname)
            tree_hash = compute_directory_hash(fullname, ls_hashes)
            tree_hash.update({
                'name': bytes(dirname, 'utf-8'),
                'perms': GitPerm.dir,
                'type': GitType.dir
            })
            dir_hashes.append(tree_hash)

        ls_hashes.update({
            dirpath: ls_hashes.get(dirpath, []) + dir_hashes
        })


    # compute the current directory hashes
    root_hash = compute_directory_hash(dir, ls_hashes)
    root_hash.update({
        'name': b'root',
        'perms': GitPerm.dir,
        'type': GitType.dir
    })
    ls_hashes.update({
        'root': [root_hash]
    })

    return ls_hashes


def write_file(file, content):
    """Write some content in a file.

    """
    with open(file, 'w') as f:
        f.write(content)


# prepare some arborescence with dirs and files to walk it
# scratch_folder_root = tempfile.mktemp(prefix='swh.loader.dir', suffix='.tmp', dir='/tmp')
scratch_folder_root = os.path.join(os.environ['HOME'], 'tmp')

# scratch_folder_foo = os.path.join(scratch_folder_root, 'foo')
# os.makedirs(scratch_folder_foo, exist_ok=True)
# scratch_folder_bar = os.path.join(scratch_folder_root, 'bar/barfoo')
# os.makedirs(scratch_folder_bar, exist_ok=True)

# scratch_file = os.path.join(scratch_folder_foo, 'quotes.md')
# write_file(scratch_file,
#            'Shoot for the moon. Even if you miss, you\'ll land among the stars.')

# scratch_file2 = os.path.join(scratch_folder_bar, 'another-quote.org')
# write_file(scratch_file2,
#            'A Victory without danger is a triumph without glory.\n-- Pierre Corneille')

def git_ls_tree_rec(hashes):
    """Display the computed result for debug purposes.

    """
    for entry in hashes.keys():
        entry_properties = hashes[entry]
        print("entry name: %s" % entry)
        for file in entry_properties:
            sha1 = hashutil.hash_to_hex(file['sha1_git'])
            print("%s %s %s\t%s" % (file['perms'].value.decode('utf-8'),
                                    file['type'].value.decode('utf-8'),
                                    sha1,
                                    file['name'].decode('utf-8')))
        print()


hashes = walk_and_compute_sha1_from_directory(scratch_folder_root)
git_ls_tree_rec(hashes)

# clean up
# shutil.rmtree(scratch_folder_root, ignore_errors = True)
