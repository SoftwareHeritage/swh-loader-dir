# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import hashlib

from io import BytesIO

from swh.core import hashutil


hashfile = hashutil.hashfile
hash_to_hex = hashutil.hash_to_hex
hex_to_hash = hashutil.hex_to_hash


def _new_hash(header_type, length):
    """Initialize a digest object (as returned by python's hashlib) for the
    git sha1 algorithm.
    This is in charge of pre-computing the needed header for git.

    Args:
        header_type: a git sha1 type ('blob', 'tree', 'commit', 'tag')
        length: Length of content to hash. Could be None if when hashing
        with sha1 and sha256

    Returns:
        A digest object

    Raises:
        ValueError if header_type is not one of 'blob', 'commit', 'tree', 'tag'

    """
    h = hashlib.new('sha1')
    if header_type not in ('blob', 'commit', 'tree', 'tag'):
        raise ValueError(
            'Only supported types are blob, commit, tree, tag')

    h.update(('%s %d\0' % (header_type, length)).encode('ascii'))

    return h


def _hash_file_obj(f, header_type, length):
    """hash (git sha1) the content of a file-like object f with header_type
    and length.

    Returns:
        A dictionary with 'sha1_git' as key and value the computed sha1_git.

    Raises:
        ValueError if header_type is not one of 'blob', 'commit', 'tree', 'tag'

    """
    h = _new_hash(header_type, length)
    while True:
        chunk = f.read(hashutil.HASH_BLOCK_SIZE)
        if not chunk:
            break
        h.update(chunk)

    return {'sha1_git': h.digest()}


def hashdata(data, header_type):
    """Hash data as git sha1 with header_type.

    Returns:
        A dictionary with 'sha1_git' as key and value the computed sha1_git.

    Raises:
        ValueError if header_type is not one of 'blob', 'commit', 'tree', 'tag'

    """
    buf = BytesIO(data)
    return _hash_file_obj(buf, header_type, len(data))
