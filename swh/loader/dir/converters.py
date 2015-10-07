# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""Convert dir objects to dictionaries suitable for swh.storage"""

from datetime import datetime

from swh.loader.dir.git.git import GitType


def format_date(signature):
    """Convert the date from a signature to a datetime"""
    return datetime.datetime.fromtimestamp(signature.time,
                                           datetime.timezone.utc)


def blob_to_content(obj, log=None, max_content_size=None, origin_id=None):
    """Convert to a compliant swh content.

    """
    size = obj['length']
    obj.update({
        'perms': obj['perms'].value,
        'type': obj['type'].value
    })

    if max_content_size and size > max_content_size:
        if log:
            log.info('Skipping content %s, too large (%s > %s)' %
                     (obj['sha1_git'], size, max_content_size))
            obj.update({'status': 'absent',
                        'reason': 'Content too large',
                        'origin': origin_id})
        return obj

    obj.update({
        'status': 'visible'
    })

    return obj


def tree_to_directory(id, repo, log=None):
    """Format a tree as a directory"""
    ret = {
        'id': id.raw,
    }
    entries = []
    ret['entries'] = entries

    entry_type_map = {
        GitType.TREE: 'dir',
        GitType.BLOB: 'file',
        GitType.COMM: 'rev',
    }

    for entry in repo[id]:
        entries.append({
            'type': entry_type_map[entry.type],
            'perms': entry.filemode,
            'name': entry.name,
            'target': entry.id.raw,
            'atime': None,
            'mtime': None,
            'ctime': None,
        })

    return ret


def commit_to_revision(id, repo, log=None):
    """Format a commit as a revision"""
    commit = repo[id]

    author = commit.author
    committer = commit.committer
    return {
        'id': id.raw,
        'date': format_date(author),
        'date_offset': author.offset,
        'committer_date': format_date(committer),
        'committer_date_offset': committer.offset,
        'type': 'git',
        'directory': commit.tree_id.raw,
        'message': commit.raw_message,
        'author_name': author.name,
        'author_email': author.email,
        'committer_name': committer.name,
        'committer_email': committer.email,
        'parents': [p.raw for p in commit.parent_ids],
    }


def ref_to_occurrence(ref):
    """Format a reference as an occurrence"""
    return ref


def origin_url_to_origin(origin_url):
    """Format a pygit2.Repository as an origin suitable for swh.storage"""
    return {
        'type': 'dir',
        'url': origin_url,
    }
