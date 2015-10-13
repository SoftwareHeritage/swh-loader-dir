# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import subprocess

from swh.core.scheduling import Task
from swh.core import config

from swh.loader.dir.loader import DirLoader



class LoadDirRepository(Task):
    """Import a directory to Software Heritage"""

    CONFIG_BASE_FILENAME = 'loader/dir.ini'
    ADDITIONAL_CONFIG = {}

    def __init__(self):
        self.config = DirLoader.parse_config_file(
            base_filename=self.CONFIG_BASE_FILENAME,
            additional_configs=[self.ADDITIONAL_CONFIG],
        )
        self.loader = DirLoader(self.config)
        self.loader.log = self.log

    def run(self, dir_path):
        """Import a directory"""
        self.loader.process(dir_path)


class LoadTarRepository(Task):
    """Import a tarball to Software Heritage"""

    CONFIG_BASE_FILENAME = 'loader-tar.ini'
    ADDITIONAL_CONFIG = {
        'dir_path': ('str', '/tmp/swh.loader.tar/'),
        'tar_path': ('str', '/some/path/to/tarball.tar')

    }

    def __init__(self):
        self.config = DirLoader.parse_config_file(
            base_filename=self.CONFIG_BASE_FILENAME,
            additional_configs=[self.ADDITIONAL_CONFIG],
        )
        config.prepare_folders(self.config, 'dir_path')
        self.loader = DirLoader(self.config)
        self.loader.log = self.log

    def untar(self, tar_path, dir_path):
        """Decompress an archive tar_path to dir_path.

        """
        subprocess.check_output(['tar', 'xvf', tar_path,
                                 '--preserve-permissions',
                                 '-C', dir_path],
                                universal_newlines=True)

    def run(self, dir_path):
        """Import a tarball.

        """
        tar_path = self.config['tar_path']
        self.untar(tar_path, dir_path)
        self.loader.process(dir_path)
