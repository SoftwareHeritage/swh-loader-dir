# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""Convert dir objects to dictionaries suitable for swh.storage"""

import datetime
import os
import sys

from swh.model.hashutil import hash_to_hex

from swh.loader.dir import git


sys_encoding = sys.getfilesystemencoding()


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
    """Convert obj to a swh storage content.

    Note:
    - If obj represents a link, the length and data are already
    provided so we use them directly.
    - 'data' is returned only if max_content_size is not reached.

    Returns:
        obj converted to content as a dictionary.

    """
    filepath = obj['path']
    if 'length' in obj:  # link already has it
        size = obj['length']
    else:
        size = os.lstat(filepath).st_size

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
                     (hash_to_hex(obj['sha1_git']),
                      size,
                      max_content_size))
        ret.update({'status': 'absent',
                    'reason': 'Content too large',
                    'origin': origin_id})
        return ret

    if 'data' in obj:  # link already has it
        data = obj['data']
    else:
        data = open(filepath, 'rb').read()

    ret.update({
        'data': data,
        'status': 'visible'
    })

    return ret


# Map of type to swh types
_entry_type_map = {
    git.GitType.TREE: 'dir',
    git.GitType.BLOB: 'file',
    git.GitType.COMM: 'rev',
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
        'date': {
            'timestamp': commit['author_date'],
            'offset': format_to_minutes(commit['author_offset']),
        },
        'committer_date': {
            'timestamp': commit['committer_date'],
            'offset': format_to_minutes(commit['committer_offset']),
        },
        'type': commit['type'],
        'directory': upper_directory['sha1_git'],
        'message': commit['message'].encode(sys_encoding),
        'author': {
            'name': commit['author_name'].encode(sys_encoding),
            'email': commit['author_email'].encode(sys_encoding),
        },
        'committer': {
            'name': commit['committer_name'].encode(sys_encoding),
            'email': commit['committer_email'].encode(sys_encoding),
        },
        'synthetic': True,
        'metadata': commit['metadata'],
        'parents': [],
    }


def annotated_tag_to_release(release, log=None):
    """Format a swh release.

    """
    return {
        'target': release['target'],
        'target_type': release['target_type'],
        'name': release['name'].encode(sys_encoding),
        'message': release['comment'].encode(sys_encoding),
        'date': {
            'timestamp': release['date'],
            'offset': format_to_minutes(release['offset']),
        },
        'author': {
            'name': release['author_name'].encode(sys_encoding),
            'email': release['author_email'].encode(sys_encoding),
        },
        'synthetic': True,
    }


def ref_to_occurrence(ref):
    """Format a reference as an occurrence"""
    occ = ref.copy()
    if 'branch' in ref:
        branch = ref['branch']
        if isinstance(branch, str):
            occ['branch'] = branch.encode(sys_encoding)
        else:
            occ['branch'] = branch
    return occ
