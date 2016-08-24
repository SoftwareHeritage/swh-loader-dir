# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.loader.dir.loader import DirLoader
from swh.scheduler.task import Task


class LoadDirRepository(Task):
    """Import a directory to Software Heritage

    """
    task_queue = 'swh_loader_dir'

    def run(self, dir_path, origin, revision, release, occurrences):
        """Import a directory.

        Args:
            cf. swh.loader.dir.loader.run docstring

        """
        DirLoader().prepare_and_load(
            dir_path, origin, revision, release, occurrences)
