# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.scheduler.task import Task

from swh.loader.dir.loader import DirLoaderWithHistory


class LoadDirRepository(Task):
    """Import a directory to Software Heritage

    """
    task_queue = 'swh_loader_dir'

    CONFIG_BASE_FILENAME = 'loader/dir.ini'
    ADDITIONAL_CONFIG = {}

    def __init__(self):
        self.config = DirLoaderWithHistory.parse_config_file(
            base_filename=self.CONFIG_BASE_FILENAME,
            additional_configs=[self.ADDITIONAL_CONFIG],
        )

    def run(self, dir_path, origin, revision, release, occurrences):
        """Import a directory.

        Args:
            cf. swh.loader.dir.loader.run docstring

        """
        loader = DirLoaderWithHistory(self.config)
        loader.log = self.log
        loader.process(dir_path, origin, revision, release, occurrences)
