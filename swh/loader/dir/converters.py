# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""Convert dir objects to dictionaries suitable for swh.storage"""

import datetime

from swh.loader.dir.git.git import GitType
from swh.loader.dir.git import git, utils


def to_datetime(ts):
    """Convert a timestamp to utc datetime.

    """
    return datetime.datetime.utcfromtimestamp(ts).replace(
        tzinfo=datetime.timezone.utc)


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


def blob_to_content(obj, log=None, max_content_size=None,
                    origin_id=None):
    if 'data' not in obj:
        filepath = obj['path']
        content_raw = open(filepath, 'rb').read()
        obj.update({'data': content_raw,
                    'length': len(content_raw)})
    return _blob_to_content(obj, log, max_content_size, origin_id)


def _blob_to_content(obj, log=None,
                     max_content_size=None,
                     origin_id=None):
    """Convert to a compliant swh content.

    """
    size = obj['length']
    ret = {
        'sha1': obj['sha1'],
        'sha256': obj['sha256'],
        'sha1_git': obj['sha1_git'],
        'length': size,
        'perms': obj['perms'].value,
        'type': obj['type'].value,
    }

    if max_content_size and size > max_content_size:
        if log:
            log.info('Skipping content %s, too large (%s > %s)' %
                     (utils.hash_to_hex(obj['sha1_git']),
                      size,
                      max_content_size))
        ret.update({'status': 'absent',
                    'reason': 'Content too large',
                    'origin': origin_id})
        return ret

    ret.update({
        'status': 'visible',
        'data': obj['data'],
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
            'perms': int(entry['perms'].value),
            'name': entry['name'],
            'target': entry['sha1_git']
        })

    return {
        'id': tree['sha1_git'],
        'entries': entries
    }


def commit_to_revision(commit, objects, log=None):
    """Format a commit as a revision.

    """
    upper_directory = objects[git.ROOT_TREE_KEY][0]
    return {
        'id': commit['sha1_git'],
        'date': to_datetime(commit['author_date']),
        'date_offset': format_to_minutes(commit['author_offset']),
        'committer_date': to_datetime(commit['committer_date']),
        'committer_date_offset': format_to_minutes(commit['committer_offset']),
        'type': commit['type'],
        'directory': upper_directory['sha1_git'],
        'message': commit['message'],
        'author_name': commit['author_name'],
        'author_email': commit['author_email'],
        'committer_name': commit['committer_name'],
        'committer_email': commit['committer_email'],
        'synthetic': True,
        'metadata': commit['metadata'],
        'parents': [],
    }


def annotated_tag_to_release(release, log=None):
    """Format a swh release.

    """
    return {
        'id': release['sha1_git'],
        'revision': release['revision'],
        'name': release['name'],
        'comment': release['comment'],
        'date': to_datetime(release['date']),
        'date_offset': format_to_minutes(release['offset']),
        'author_name': release['author_name'],
        'author_email': release['author_email'],
        'synthetic': True,
    }
