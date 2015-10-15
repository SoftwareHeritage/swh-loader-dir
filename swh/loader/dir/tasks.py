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

        # occurrence information
        'branch': ('str', 'master'),
        'authority_id': ('int', 1),
        'validity': ('str', '2015-01-01 00:00:00+00'),

        # revision information
        'revision_author_name': ('str', 'swh author'),
        'revision_author_email': ('str', 'swh@inria.fr'),
        'revision_author_date': ('int', 1444054085),
        'revision_author_offset': ('str', '+0200'),
        'revision_committer_name': ('str', 'swh committer'),
        'revision_committer_email': ('str', 'swh@inria.fr'),
        'revision_committer_date': ('int', 1444054085),
        'revision_committer_offset': ('str', '+0200'),
        'revision_type': ('str', 'tar'),
        'revision_message': ('str', 'synthetic revision'),

        # release information
        'release_name': ('str', 'v0.0.1'),
        'release_date': ('int', 1444054085),
        'release_offset': ('str', '+0200'),
        'release_author_name': ('str', 'swh author'),
        'release_author_email': ('str', 'swh@inria.fr'),
        'release_comment': ('str', 'synthetic release'),
    }

    def run(self, tar_path):
        """Import a tarball tar_path.

        """
        info = {}
        for key in ['dir_path',
                    # origin
                    'branch', 'authority_id', 'validity',
                    # revision
                    'revision_author_name', 'revision_author_email',
                    'revision_author_date', 'revision_author_offset',
                    'revision_committer_name', 'revision_committer_email',
                    'revision_committer_date', 'revision_committer_offset',
                    'revision_type', 'revision_message',
                    # release
                    'release_name', 'release_date', 'release_offset',
                    'release_author_name', 'release_author_email',
                    'release_comment']:
            info.update({key: self.config[key]})

        init_dir_path = self.config['dir_path']
        dir_path = tempfile.mkdtemp(prefix='swh.loader.tar', dir=init_dir_path)

        # unarchive in dir_path
        untar(tar_path, dir_path)

        # Update the origin's url
        # and the dir_path to load
        origin_url = 'file://' + tar_path
        info.update({
            'origin_url': origin_url,
            'dir_path': dir_path
        })

        # Load the directory result
        try:
            super().run(info)
        finally:  # always clean up
            shutil.rmtree(dir_path)
