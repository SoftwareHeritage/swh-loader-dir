# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from celery import current_app as app

from swh.loader.dir.loader import DirLoader


@app.task(name=__name__ + '.LoadDirRepository')
def load_directory(dir_path, origin, visit_date, revision, release,
                   branch_name=None):
    """Import a directory to Software Heritage

    Import a directory dir_path with origin at visit_date time.
    Providing the revision, release, and occurrences.

    """
    return DirLoader().load(dir_path=dir_path, origin=origin,
                            visit_date=visit_date, revision=revision,
                            release=release, branch_name=branch_name)
