# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import subprocess

from swh.core.scheduling import Task
from swh.core import config

from swh.loader.dir.loader import DirLoader


class LoadDirRepository(Task):
    """Import a directory to Software Heritage

    """
    task_queue = 'swh_loader_dir'

    CONFIG_BASE_FILENAME = 'loader/dir.ini'
    ADDITIONAL_CONFIG = {}

    def __init__(self):
        self.config = DirLoader.parse_config_file(
            base_filename=self.CONFIG_BASE_FILENAME,
            additional_configs=[self.ADDITIONAL_CONFIG],
        )

    def run(self, info):
        """Import a directory.

        Args:
            info: Dictionary of information needed, keys are:
              - dir_path: directory to import
              - origin_url: origin url (e.g file:///dev/null)
              - branch: occurrence's branch name
              - authority_id: authority id (e.g. 1 for swh)
              - validity: validity date (e.g. 2015-01-01 00:00:00+00)
              - revision_author_name: revision's author name
              - revision_author_email: revision's author email
              - revision_author_date: timestamp (e.g. 1444054085)
              - revision_author_offset: date offset e.g. -0220, +0100
              - revision_committer_name: revision's committer name
              - revision_committer_email: revision's committer email
              - revision_committer_date: timestamp
              - revision_committer_offset: date offset e.g. -0220, +0100
              - revision_type: type of revision dir, tar
              - revision_message: synthetic message for the revision
              - release_name: release name
              - release_date: release timestamp (e.g. 1444054085)
              - release_offset: release date offset e.g. -0220, +0100
              - release_author_name: release author's name
              - release_author_email: release author's email
              - release_comment: release's comment message

        """
        loader = DirLoader(self.config)
        loader.log = self.log
        loader.process(info)


def untar(tar_path, dir_path):
    """Decompress an archive tar_path to dir_path.

    At the end of this call, dir_path contains the tarball's
    uncompressed content.

    Args:
        tar_path: the path to access the tarball
        dir_path: The path where to extract the tarball's content.
    """
    untar_cmd = ['tar', 'xavf', tar_path,
                 '--preserve-permissions',
                 '-C', dir_path]
    subprocess.check_call(untar_cmd, stderr=subprocess.STDOUT)


class LoadTarRepository(LoadDirRepository):
    """Import a tarball to Software Heritage

    """
    task_queue = 'swh_loader_tar'

    CONFIG_BASE_FILENAME = 'loader/tar.ini'
    ADDITIONAL_CONFIG = {
        'dir_path': ('str', '/tmp/swh.loader.tar/'),
        'tar_path': ('str', '/some/path/to/tarball.tar')
    }

    def run(self, info):
        """Import a tarball.

        """
        config.prepare_folders(self.config, 'dir_path')
        untar(info['tar_path'], info['dir_path'])
        super().run(info)
