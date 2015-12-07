# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import os

from swh.core import hashutil


hashfile = hashutil.hashfile
hash_to_hex = hashutil.hash_to_hex
hex_to_hash = hashutil.hex_to_hash


def hashdata(data, header_type):
    """Hash data as git sha1 with header_type.

    Returns:
        A dictionary with 'sha1_git' as key and value the computed sha1_git.

    Raises:
        ValueError if header_type is not one of 'blob', 'commit', 'tree', 'tag'

    """
    hashobj = hashutil.hash_git_object(data, header_type)
    return {
        'sha1_git': hashobj.digest(),
    }


def hashlink(linkpath):
    """Compute hashes for a link.

    Args:
        linkpath: the absolute path name to a symbolic link.

    Returns:
        dictionary with sha1_git as key and the actual binary sha1 as value.

    """
    raw_data = os.readlink(linkpath)
    hashes = hashutil.hashdata(raw_data)
    hashes.update({
        'data': raw_data,
        'length': len(raw_data)
    })
    return hashes
