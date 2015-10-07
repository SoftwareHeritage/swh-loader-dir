# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""Convert dir objects to dictionaries suitable for swh.storage"""

from datetime import datetime

from swh.loader.dir.git.git import GitType


def format_to_minutes(offset_str):
    """Convert a git string timezone format string (e.g  +0200, -0310) to minutes.

    Args:
        offset_str: a string representing an offset.

    Returns:
        A positive or negative number of minutes of such input

    """
    sign = offset_str[0]
    hours = int(offset_str[1:3])
    minutes = int(offset_str[3:]) + (hours * 60)
    return minutes if sign == '+' else -1 * minutes


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


def commit_to_revision(commit, objects, log=None):
    """Format a commit as a revision.

    """
    upper_directory = objects['<root>'][0]
    return {
        'id': commit['sha1_git'],
        'date':
          datetime.fromtimestamp(commit['revision_author_date']),
        'date_offset':
          format_to_minutes(commit['revision_author_offset']),
        'committer_date':
          datetime.fromtimestamp(commit['revision_committer_date']),
        'committer_date_offset':
          format_to_minutes(commit['revision_committer_offset']),
        'type': commit['revision_type'],
        'directory': upper_directory['sha1_git'],
        'message': commit['revision_message'],
        'author_name': commit['revision_author_name'],
        'author_email': commit['revision_author_email'],
        'committer_name': commit['revision_committer_name'],
        'committer_email': commit['revision_committer_email'],
        'parents': [],
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
