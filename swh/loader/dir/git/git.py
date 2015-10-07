# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import os

from enum import Enum

from swh.loader.dir.git import utils


class GitType(Enum):
    BLOB = b'blob'
    TREE = b'tree'
    EXEC = b'exec'
    LINK = b'link'
    COMM = b'commit'
    RELE = b'release'


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
            dictionary with sha1_git as key and the actual binary sha1 as value.

        Assumes:
            Every path exists in hashes.

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


def compute_revision_git_sha1(hashes, info):
    """Compute a revision's hash.

    Use the <root> entry's sha1_git as tree representation.

    Args:
        hashes:
        info: Additional dictionary information needed to compute a synthetic
        revision. Following keys are expected:
            - revision_author_name
            - revision_author_email
            - revision_author_date
            - revision_author_offset
            - revision_committer_name
            - revision_committer_email
            - revision_committer_date
            - revision_committer_offset
            - revision_message
            - revision_type


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
    hashes = utils.hashdata(revision_content, 'commit')
    hashes.update({
        'revision_author_name': info['revision_author_name'],
        'revision_author_email': info['revision_author_email'],
        'revision_author_date': info['revision_author_date'],
        'revision_author_offset': info['revision_author_offset'],
        'revision_committer_name': info['revision_committer_name'],
        'revision_committer_email': info['revision_committer_email'],
        'revision_committer_date': info['revision_committer_date'],
        'revision_committer_offset': info['revision_committer_offset'],
        'revision_message': info['revision_message'],
        'revision_type': info['revision_type']
    })
    return hashes


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
        'name': bytes(os.path.basename(linkpath), 'utf-8'),
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
    m_hashes.update({
        'name': bytes(os.path.basename(filepath), 'utf-8'),
        'perms': GitPerm.EXEC if os.access(filepath, os.X_OK) else GitPerm.BLOB,
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
        'name': bytes(os.path.basename(dirname), 'utf-8'),
        'perms': GitPerm.TREE,
        'type': GitType.TREE,
        'path': dirname
    })
    return tree_hash


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
    empty_dirs = set()
    link_dirs = set()

    for dirpath, dirnames, filenames in os.walk(rootdir, topdown=False):
        hashes = []

        if not(dirnames) and not(filenames):
            empty_dirs.add(dirpath)
            continue

        links = [ file for file in filenames
                    if os.path.islink(os.path.join(dirpath, file)) ] + \
                [ dir for dir in dirnames
                    if os.path.islink(os.path.join(dirpath, dir))]

        for link in links:
            linkpath = os.path.join(dirpath, link)
            link_dirs.add(linkpath)
            m_hashes = compute_link_metadata(linkpath)
            hashes.append(m_hashes)

        for filename in [ file for file in filenames
                            if os.path.join(dirpath, file) not in link_dirs ]:
            filepath = os.path.join(dirpath, filename)
            m_hashes = compute_blob_metadata(filepath)
            hashes.append(m_hashes)

        ls_hashes.update({
            dirpath: hashes
        })

        dir_hashes = []
        subdirs = [ dir for dir in dirnames
                       if os.path.join(dirpath, dir)
                         not in (empty_dirs | link_dirs) ]
        for dirname in subdirs:
            fulldirname = os.path.join(dirpath, dirname)
            tree_hash = compute_tree_metadata(fulldirname, ls_hashes)
            dir_hashes.append(tree_hash)

        ls_hashes.update({
            dirpath: ls_hashes.get(dirpath, []) + dir_hashes
        })

    # compute the current directory hashes
    root_hash = compute_directory_git_sha1(rootdir, ls_hashes)
    root_hash.update({
        'path': rootdir,
        'name': bytes(os.path.basename(rootdir), 'utf-8'),
        'perms': GitPerm.TREE,
        'type': GitType.TREE
    })
    ls_hashes.update({
        '<root>': [root_hash]
    })

    return ls_hashes
