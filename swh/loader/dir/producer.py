# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re
import itertools


def init_archive_extension_pattern(exts):
    """Given a list of extensions, return the regexp for exts.

    """
    res = []
    for p, pp in itertools.product(exts, repeat=2):
        res.append('\.' + '\.'.join([p, pp]))
    for p in exts:
        res.append(''.join(['\.' + p]))

    return '|'.join(res)


# FIXME; extract this in property
# to recognize existing naming pattern
archive_extension_patterns = [
    'zip',
    'tar',
    'gz', 'tgz',
    'bz2', 'bzip2',
    'lzma', 'lz',
    'xz',
    'Z',
]


re_archive_patterns = re.compile(
    init_archive_extension_pattern(archive_extension_patterns),
    flags=re.IGNORECASE)
software_name_pattern = re.compile('([a-zA-Z-_]*[0-9]*[a-zA-Z-_]*)')
digit_pattern = re.compile('[0-9]')
release_pattern = re.compile('[0-9.]+')


def _extension(filename):
    m = re_archive_patterns.search(filename)
    if m:
        return m.group()


def release_number(filename):
    """Compute the release number from the filename.

    """
    name = _software_name(filename)
    ext = _extension(filename)
    if not ext:
        return None
    version = filename.replace(name, '').replace(ext, '')
    if version:
        # some filename use . for delimitation
        # not caught by regexp so filtered here
        if version[0] == '.':
            version = version[1:]  # arf
        if not release_pattern.match(version):  # check pattern release
            return None
        return version
    return None


def _software_name(filename):
    """Compute the software name from the filename.

    """
    m = software_name_pattern.match(filename)
    res = m.group()
    if digit_pattern.match(res[-1]):  # remains first version number
        return res[0:-1]
    return res
