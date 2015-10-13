# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core.scheduling import Task

from .loader import DirLoader


class LoadDirRepository(Task):
    """Import a directory to Software Heritage"""

    CONFIG_BASE_FILENAME = 'loader/dir.ini'
    ADDITIONAL_CONFIG = {}

    def __init__(self):
        self.config = DirLoader.parse_config_file(
            base_filename=self.CONFIG_BASE_FILENAME,
            additional_configs=[self.ADDITIONAL_CONFIG],
        )

    def run(self, repo_path, origin_url, authority_id, validity):
        """Import a directory"""
        loader = DirLoader(self.config)
        loader.log = self.log

        loader.process(repo_path)
