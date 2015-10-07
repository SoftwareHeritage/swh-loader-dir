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


def blob_to_content(obj, objects, log=None, max_content_size=None, origin_id=None):
    """Convert to a compliant swh content.

    """
    size = obj['length']
    ret = {
        'sha1': obj['sha1'],
        'sha256': obj['sha256'],
        'sha1_git': obj['sha1_git'],
        'data': obj['data'],
        'length': size,
        'perms': obj['perms'].value,
        'type': obj['type'].value
    }

    if max_content_size and size > max_content_size:
        if log:
            log.info('Skipping content %s, too large (%s > %s)' %
                     (obj['sha1_git'], size, max_content_size))
            ret.update({'status': 'absent',
                        'reason': 'Content too large',
                        'origin': origin_id})
        return ret

    ret.update({
        'status': 'visible'
    })

    return ret


# Map of type to swh types
_entry_type_map = {
    GitType.TREE: 'dir',
    GitType.BLOB: 'file',
    GitType.COMM: 'rev',
}


def tree_to_directory(tree, objects, log=None):
    """Format a tree as a directory

    """
    entries = []
    for entry in objects[tree['path']]:
        entries.append({
            'type': _entry_type_map[entry['type']],
            'perms': entry['perms'].value,
            'name': entry['name'],
            'target': entry['sha1_git'],
            'atime': None,
            'mtime': None,
            'ctime': None,
        })

    return {
        'id': tree['sha1_git'],
        'perms': tree['perms'].value,
        'type': tree['type'].value,
        'entries': entries
    }


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
