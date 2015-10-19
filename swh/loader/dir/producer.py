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


# def filter_out_release_number(filename):
#     filtered_data = filter(lambda x: len(x) > 1,
#                            re.findall('[-.a-zA-Z_]*', filename))
#     return list(filtered_data)


# def compute_release_software_ext(filename):
#     return filter_out_release_number(filename)[-1]


# def compute_release_number_2(filename):
#     data_to_filter = filter_out_release_number(filename)
#     version_number = filename
#     for s in data_to_filter:
#         version_number = version_number.strip(s)

#     return version_number if version_number else None


# def compute_release_number_3(filename):
#     res = re.findall('[-_]([0-9.a-z+-]+)(\.*){1,2}', filename)
#     if res:
#         return res[0]

# def release_number(filename):
#     """Compute the release number from a filename.

#     First implementation without all use cases ok.

#     """
#     filtered_version = list(filter(lambda s: len(s) > 2,
#                                    re.split('[a-zA-Z]', filename)))
#     if not filtered_version:
#         return None

#     version = filtered_version[0][1:-1]

#     if version[0] == '-':  # package name contains a number in name
#         return version[1:]

#     if version[-1] == '-':
#         return version[0:-1]

#     if version[-1] in ['.', '+']:  # string alongside version
#         return release_number_2(filename)

#     return version

# special_case_patterns = [
#     'x86',
#     'x86_64',
#     'x64',
#     'i386',
#     'i686',
#     'AIX',
#     'BSD',
#     'SGI',
#     'SUN',
#     'HP-UX',
#     'HP',
#     'SunOS',
#     'w32',
#     'win32',
#     'pre',
#     'alpha',
#     'epsilon',
#     'beta',
# ]
