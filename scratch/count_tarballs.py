#!/usr/bin/env python3

import os

from swh.loader.dir import producer


def is_tarball(filename):
    """Determine if the filename is an tarball or not.

    This is dependent on the filename only.

    Args:
        filename: the filename without any paths.

    Returns:
        Boolean True if an tarball, False otherwise.

    """
    return any(map(lambda ext: filename.endswith(ext),
                   producer.archive_extension_patterns))

def list_tarballs_from(path):
    """From path, produce tarball tarball message to celery.

    Args:
        path: top directory to list tarballs from.

    """
    for dirpath, dirnames, filenames in os.walk(path):
        for fname in filenames:
            if is_tarball(fname):
                yield dirpath, fname

def count_tarballs_from(path):
    count = 0
    for dirpath, fname in list_tarballs_from(path):
        count += 1

    return count

if __name__ == '__main__':
    for path in ['/home/storage/space/mirrors/gnu.org/gnu',
                 '/home/storage/space/mirrors/gnu.org/old-gnu']:
        print("%s %s" % (path, count_tarballs_from(path)))
