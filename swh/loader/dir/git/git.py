# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import os

from enum import Enum

from swh.loader.dir.git import utils

from swh.model.identifiers import release_identifier, revision_identifier


ROOT_TREE_KEY = b''


class GitType(Enum):
    BLOB = b'blob'
    TREE = b'tree'
    EXEC = b'exec'
    LINK = b'link'
    COMM = b'commit'
    RELE = b'release'
    REFS = b'ref'


class GitPerm(Enum):
    BLOB = b'100644'
    TREE = b'40000'
    EXEC = b'100755'
    LINK = b'120000'


def compute_directory_git_sha1(dirpath, hashes):
    """Compute a directory git sha1 for a dirpath.

    Args:
        dirpath: the directory's absolute path
        hashes: list of tree entries with keys:
            - sha1_git: the tree entry's sha1
            - name: file or subdir's name
            - perms: the tree entry's sha1 permissions

        Returns:
            dictionary with sha1_git as key and the actual binary sha1 as
            value.

        Assumes:
            Every path exists in hashes.

    """
    def sorted_key_fn(entry):
        """Beware the sorted algorithm in git add a / for tree entries.

        """
        name = entry['name']
        return name + b'/' if entry['type'] is GitType.TREE else name

    def sort_by_entry_name(hashes):
        return sorted(hashes, key=sorted_key_fn)

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


def compute_revision_sha1_git(revision):
    """Compute a revision sha1 git from its dict representation.

    Args:
        revision: Additional dictionary information needed to compute a
        synthetic
        revision. Following keys are expected:
            - author
            - date
            - committer
            - committer_date
            - message
            - type
            - directory: binary form of the tree hash

    Returns:
        revision sha1 in bytes

    # FIXME: beware, bytes output from storage api

    """
    return bytes.fromhex(revision_identifier(revision))


def compute_release_sha1_git(release):
    """Compute a release sha1 git from its dict representation.

    Args:
        release: Additional dictionary information needed to compute a
        synthetic release. Following keys are expected:
            - name
            - message
            - date
            - author
            - revision: binary form of the sha1_git revision targeted by this

    Returns:
        release sha1 in bytes

    """
    return bytes.fromhex(release_identifier(release))


def compute_link_metadata(linkpath):
    """Given a linkpath, compute the git metadata.

    Args:
        linkpath: absolute pathname of the link

    Returns:
        Dictionary of values:
            - name: basename of the link
            - perms: git permission for link
            - type: git type for link
    """
    m_hashes = utils.hashlink(linkpath)
    m_hashes.update({
        'name': os.path.basename(linkpath),
        'perms': GitPerm.LINK,
        'type': GitType.BLOB,
        'path': linkpath
    })
    return m_hashes


def compute_blob_metadata(filepath):
    """Given a filepath, compute the git metadata.

    Args:
        filepath: absolute pathname of the file.

    Returns:
        Dictionary of values:
            - name: basename of the file
            - perms: git permission for file
            - type: git type for file

    """
    m_hashes = utils.hashfile(filepath)
    perms = GitPerm.EXEC if os.access(filepath, os.X_OK) else GitPerm.BLOB
    m_hashes.update({
        'name': os.path.basename(filepath),
        'perms': perms,
        'type': GitType.BLOB,
        'path': filepath
    })
    return m_hashes


def compute_tree_metadata(dirname, ls_hashes):
    """Given a dirname, compute the git metadata.

    Args:
        dirname: absolute pathname of the directory.

    Returns:
        Dictionary of values:
            - name: basename of the directory
            - perms: git permission for directory
            - type: git type for directory

    """
    tree_hash = compute_directory_git_sha1(dirname, ls_hashes)
    tree_hash.update({
        'name': os.path.basename(dirname),
        'perms': GitPerm.TREE,
        'type': GitType.TREE,
        'path': dirname
    })
    return tree_hash


def walk_and_compute_sha1_from_directory(rootdir):
    """Compute git sha1 from directory rootdir.

    Returns:
        Dictionary of entries with keys <path-name> and as values a list of
        directory entries.
        Those are list of dictionary with keys:
          - 'perms'
          - 'type'
          - 'name'
          - 'sha1_git'
          - and specifically content: 'sha1', 'sha256', ...

    Note:
        One special key is ROOT_TREE_KEY to indicate the upper root of the
        directory (this is the revision's directory).

    Raises:
        Nothing
        If something is raised, this is a programmatic error.

    """
    ls_hashes = {}
    all_links = set()

    for dirpath, dirnames, filenames in os.walk(rootdir, topdown=False):
        hashes = []

        links = [os.path.join(dirpath, file)
                 for file in (filenames+dirnames)
                 if os.path.islink(os.path.join(dirpath, file))]

        for linkpath in links:
            all_links.add(linkpath)
            m_hashes = compute_link_metadata(linkpath)
            hashes.append(m_hashes)

        only_files = [os.path.join(dirpath, file)
                      for file in filenames
                      if os.path.join(dirpath, file) not in all_links]
        for filepath in only_files:
            m_hashes = compute_blob_metadata(filepath)
            hashes.append(m_hashes)

        ls_hashes.update({
            dirpath: hashes
        })

        dir_hashes = []
        subdirs = [os.path.join(dirpath, dir)
                   for dir in dirnames
                   if os.path.join(dirpath, dir)
                   not in all_links]
        for fulldirname in subdirs:
            tree_hash = compute_tree_metadata(fulldirname, ls_hashes)
            dir_hashes.append(tree_hash)

        ls_hashes.update({
            dirpath: ls_hashes.get(dirpath, []) + dir_hashes
        })

    # compute the current directory hashes
    root_hash = compute_directory_git_sha1(rootdir, ls_hashes)
    root_hash.update({
        'path': rootdir,
        'name': os.path.basename(rootdir),
        'perms': GitPerm.TREE,
        'type': GitType.TREE
    })
    ls_hashes.update({
        ROOT_TREE_KEY: [root_hash]
    })

    return ls_hashes
