#!/usr/bin/env python3

import os
import shutil
import tempfile

from swh.core import hashutil
from swh.loader.dir import git
from swh.loader.dir.git import GitPerm, GitType


def compute_content_hashes(dirpath, filename):
    """Given a dirpath and a filename, compute the hashes for that particular
    file.

    Args:
        dirpath: the absolute path of the filename
        filename: the file's name

    Returns:
        The computed hashes for that dirpath/filename.

    Assumes:
        The full computed path of the file exists.

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


def walk_and_compute_sha1_from_directory(rootdir):
    """Compute git sha1 from directory rootdir.

    Empty directories are skipped.

    Returns:
        Dictionary of entries with keys <path-name> and as values a list of
        directory entries.
        Those are list of dictionary with keys:
          - 'perms'
          - 'type'
          - 'name'
          - 'sha1_git'
          - and specifically content: 'sha1', 'sha256', ... (may be extended...)

    Note:
        One special key is '<root>' to indicate the upper root of the directory.
        (This is typically the entry point of the revision).

    Raises:
        Nothing
        If something is raised, this is a programmatic error.

    """
    ls_hashes = {}
    empty_dir = set()

    for dirpath, dirnames, filenames in os.walk(rootdir, topdown=False):
        hashes = []

        if dirnames == [] and filenames == []:
            empty_dir.add(dirpath)
            continue

        # compute content hashes
        for filename in filenames:
            m_hashes = compute_content_hashes(dirpath, filename)
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
        # compute directory hashes and skip empty ones
        for dirname in [dir for dir in dirnames if os.path.join(dirpath, dir) not in empty_dir]:
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
    root_hash = compute_directory_hash(rootdir, ls_hashes)
    root_hash.update({
        'name': bytes(rootdir, 'utf-8'),
        'perms': GitPerm.dir,
        'type': GitType.dir
    })
    ls_hashes.update({
        '<root>': [root_hash]
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


def compute_revision_hash(hashes, info):
    """Compute a revision's hash.

    Use the <root> entry's sha1_git as tree representation.

    """
    tree_hash = hashutil.hash_to_hex(hashes['<root>'][0]['sha1_git'])

    revision_content = ("""tree %s
author %s <%s> %s %s
committer %s <%s> %s %s

%s
""" % (tree_hash,
         info['revision_author_name'],
         info['revision_author_email'],
         info['revision_author_date'],
         info['revision_author_offset'],
         info['revision_committer_name'],
         info['revision_committer_email'],
         info['revision_committer_date'],
         info['revision_committer_offset'],
         info['revision_message'])).encode('utf-8')
    return git.hashdata(revision_content, 'commit')

hashes = walk_and_compute_sha1_from_directory(scratch_folder_root)
git_ls_tree_rec(hashes)

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

print('revision directory: %s' % compute_revision_hash(hashes, ADDITIONAL_INFO))

# clean up
# shutil.rmtree(scratch_folder_root, ignore_errors = True)
