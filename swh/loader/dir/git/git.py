# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import os

from enum import Enum

from . import utils


class GitType(Enum):
    file = b'blob'
    dir = b'tree'
    exec = b'exec'
    link = b'link'
    gitlink = b'gitlink'


class GitPerm(Enum):
    file = b'100644'
    dir = b'40000'
    exec = b'100755'
    link = b'120000'
    gitlink = b'160000'


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
    return utils.hashdata(b''.join(rows), 'tree')


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
    def compute_git_perms(fpath):
        """Given a filepath fpath, returns the git permissions associated.

        Args:
            fpath: absolute file (not directory) path

        Returns:
            Git equivalent permissions as in git.GitPerm enum.

        """
        if os.path.islink(fpath):
            perms = GitPerm.link
        elif os.access(fpath, os.X_OK):
            perms = GitPerm.exec
        else:
            perms = GitPerm.file

        return perms

    ls_hashes = {}
    empty_dir = set()

    for dirpath, dirnames, filenames in os.walk(rootdir, topdown=False):
        hashes = []

        if dirnames == [] and filenames == []:
            empty_dir.add(dirpath)
            continue

        # compute content hashes
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            m_hashes = utils.hashfile(filepath)
            m_hashes.update({
                'name': bytes(filename, 'utf-8'),
                'perms': compute_git_perms(filepath),
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


def compute_revision_hash(hashes, info):
    """Compute a revision's hash.

    Use the <root> entry's sha1_git as tree representation.

    """
    tree_hash = utils.hash_to_hex(hashes['<root>'][0]['sha1_git'])

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
    return utils.hashdata(revision_content, 'commit')
