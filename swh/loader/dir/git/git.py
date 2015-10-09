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


def compute_revision_git_sha1(tree_hash, info):
    """Compute a revision representation targeting the tree_hash.


    Args:
        tree_hash: binary form of the tree hash
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
    revision_author_name = info['revision_author_name']
    revision_author_email = info['revision_author_email']
    revision_author_date = info['revision_author_date']
    revision_author_offset = info['revision_author_offset']
    revision_committer_name = info['revision_committer_name']
    revision_committer_email = info['revision_committer_email']
    revision_committer_date = info['revision_committer_date']
    revision_committer_offset = info['revision_committer_offset']
    revision_message = info['revision_message']

    revision_content = ("""tree %s
author %s <%s> %s %s
committer %s <%s> %s %s

%s
""" % (utils.hash_to_hex(tree_hash),
       revision_author_name,
       revision_author_email,
       revision_author_date,
       revision_author_offset,
       revision_committer_name,
       revision_committer_email,
       revision_committer_date,
       revision_committer_offset,
       revision_message)).encode('utf-8')
    hashes = utils.hashdata(revision_content, 'commit')

    # and update other information
    hashes.update({
        'revision_author_name': revision_author_name,
        'revision_author_email': revision_author_email,
        'revision_author_date': revision_author_date,
        'revision_author_offset': revision_author_offset,
        'revision_committer_name': revision_committer_name,
        'revision_committer_email': revision_committer_email,
        'revision_committer_date': revision_committer_date,
        'revision_committer_offset': revision_committer_offset,
        'revision_message': revision_message,
        'revision_type': info['revision_type']
    })
    return hashes


def compute_release(revision_hash, info):
    """Compute a release representation.
    This release representation will contain the computed sha1_git for such
    release.

    This release will point to the revision_hash.
    The additional informations are present in the dictionary info.

    Args:
        revision_hash: binary form of the sha1_git revision targeted by this
        release
        info: Additional dictionary information needed to compute a synthetic
        release. Following keys are expected:
            - release_name
            - release_comment
            - release_date
            - release_offset
            - release_author_name
            - release_author_email

    """
    release_name = info['release_name']
    release_author_name = info['release_author_name']
    release_author_email = info['release_author_email']
    release_date = info['release_date']
    release_offset = info['release_offset']
    release_comment = info['release_comment']

    release_content_to_hash = ("""object %s
type commit
tag %s
tagger %s <%s> %s %s

%s
""" % (utils.hash_to_hex(revision_hash),
       release_name,
       release_author_name,
       release_author_email,
       release_date,
       release_offset,
       release_comment)).encode('utf-8')

    hashes = utils.hashdata(release_content_to_hash, 'tag')
    hashes.update({
        'revision_sha1_git': revision_hash,
        'release_name': release_name,
        'release_comment': release_comment,
        'release_date': release_date,
        'release_offset': release_offset,
        'release_author_name': release_author_name,
        'release_author_email': release_author_email,
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
    perms = GitPerm.EXEC if os.access(filepath, os.X_OK) else GitPerm.BLOB
    m_hashes.update({
        'name': bytes(os.path.basename(filepath), 'utf-8'),
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
        'name': bytes(os.path.basename(dirname), 'utf-8'),
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
        One special key is '<root>' to indicate the upper root of the
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
        'name': bytes(os.path.basename(rootdir), 'utf-8'),
        'perms': GitPerm.TREE,
        'type': GitType.TREE
    })
    ls_hashes.update({
        '<root>': [root_hash]
    })

    return ls_hashes
