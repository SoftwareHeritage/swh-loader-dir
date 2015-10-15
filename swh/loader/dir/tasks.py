# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import subprocess
import shutil
import tempfile

from swh.core.scheduling import Task

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

    def run(self, dir_path, origin, revision, release, occurrence):
        """Import a directory.

        Args:
            - dir_path: source of the directory to import
            - origin: Dictionary origin
              - url: url origin we fetched
              - type: type of the origin
            - revision: Dictionary of information needed, keys are:
              - author_name: revision's author name
              - author_email: revision's author email
              - author_date: timestamp (e.g. 1444054085)
              - author_offset: date offset e.g. -0220, +0100
              - committer_name: revision's committer name
              - committer_email: revision's committer email
              - committer_date: timestamp
              - committer_offset: date offset e.g. -0220, +0100
              - type: type of revision dir, tar
              - message: synthetic message for the revision
            - release: Dictionary of information needed, keys are:
              - name: release name
              - date: release timestamp (e.g. 1444054085)
              - offset: release date offset e.g. -0220, +0100
              - author_name: release author's name
              - author_email: release author's email
              - comment: release's comment message
            - occurrence: Dictionary of information needed, keys are:
              - branch: occurrence's branch name
              - authority_id: authority id (e.g. 1 for swh)
              - validity: validity date (e.g. 2015-01-01 00:00:00+00)

        """
        loader = DirLoader(self.config)
        loader.log = self.log
        loader.process(dir_path, origin, revision, release, occurrence)


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
        'extraction_dir': ('str', '/tmp/swh.loader.tar/'),

        # # occurrence information
        # 'branch': ('str', 'master'),
        # 'authority_id': ('int', 1),
        # 'validity': ('str', '2015-01-01 00:00:00+00'),

        # # revision information
        # 'revision_type': ('str', 'tar'),

        # 'revision_author_name': ('str', 'swh author'),
        # 'revision_author_email': ('str', 'swh@inria.fr'),
        # 'revision_author_date': ('int', 1444054085),
        # 'revision_author_offset': ('str', '+0200'),
        # 'revision_committer_name': ('str', 'swh committer'),
        # 'revision_committer_email': ('str', 'swh@inria.fr'),
        # 'revision_committer_date': ('int', 1444054085),
        # 'revision_committer_offset': ('str', '+0200'),
        # 'revision_message': ('str', 'synthetic revision'),

        # # release information
        # 'release_name': ('str', 'v0.0.1'),
        # 'release_date': ('int', 1444054085),
        # 'release_offset': ('str', '+0200'),
        # 'release_author_name': ('str', 'swh author'),
        # 'release_author_email': ('str', 'swh@inria.fr'),
        # 'release_comment': ('str', 'synthetic release'),
    }

    def run(self, tar_path, origin_url, revision, release, occurrence):
        """Import a tarball tar_path.

        Args:
            - tar_path: path access to the tarball
            - origin_url: url where we fetched the tarball
            - revision, release, occurrence: see LoadDirRepository.run

        """
        extraction_dir = self.config['extraction_dir']
        dir_path = tempfile.mkdtemp(prefix='swh.loader.tar',
                                    dir=extraction_dir)

        # unarchive in dir_path
        untar(tar_path, dir_path)

        origin = {
            'url': origin_url,
            'type': 'tar'
        }

        try:
            super().run(dir_path, origin, revision, release, occurrence)
        finally:  # always clean up
            shutil.rmtree(dir_path)
