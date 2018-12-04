# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import pytest

from swh.loader.core.tests import BaseLoaderTest, LoaderNoStorage
from swh.loader.dir.loader import DirLoader


@pytest.mark.fs
class BaseDirLoaderTest(BaseLoaderTest):
    def setUp(self, archive_name='sample-folder.tgz'):
        super().setUp(archive_name=archive_name,
                      prefix_tmp_folder_name='swh.loader.dir.',
                      start_path=os.path.dirname(__file__))


class DirLoaderNoStorage(LoaderNoStorage, DirLoader):
    """A DirLoader with no persistence.

    Context:
        Load a tarball with a persistent-less tarball loader

    """
    def __init__(self, config={}):
        super().__init__(config=config)
        self.origin_id = 1
        self.visit = 1


class DirLoaderListRepoObject(BaseDirLoaderTest):
    def setUp(self):
        super().setUp()

        self.info = {
            'storage': {
                'cls': 'remote',
                'args': {
                    'url': 'http://localhost:5002/',
                }
            },
            'content_size_limit': 104857600,
            'log_db': 'dbname=softwareheritage-log',
            'directory_packet_size': 25000,
            'content_packet_size': 10000,
            'send_contents': True,
            'send_directories': True,
            'content_packet_size_bytes': 1073741824,
            'send_revisions': True,
            'revision_packet_size': 100000,
            'content_packet_block_size_bytes': 104857600,
            'send_snapshot': True,
            'release_packet_size': 100000,
            'send_releases': True
        }

        self.origin = {
            'url': 'file:///dev/null',
            'type': 'dir',
        }

        self.revision = {
            'author': {
                'name': 'swh author',
                'email': 'swh@inria.fr',
                'fullname': 'swh'
            },
            'date': {
                'timestamp': 1444054085,
                'offset': 0
            },
            'committer': {
                'name': 'swh committer',
                'email': 'swh@inria.fr',
                'fullname': 'swh'
            },
            'committer_date': {
                'timestamp': 1444054085,
                'offset': 0,
            },
            'type': 'tar',
            'message': 'synthetic revision',
            'metadata': {'foo': 'bar'},
        }

        self.release = {
            'name': 'v0.0.1',
            'date': {
                'timestamp': 1444054085,
                'offset': 0,
            },
            'author': {
                'name': 'swh author',
                'fullname': 'swh',
                'email': 'swh@inria.fr',
            },
            'message': 'synthetic release',
        }

        self.dirloader = DirLoaderNoStorage(config=self.info)

    def test_load_without_storage(self):
        """List directory objects without loading should be ok"""
        # when
        dir_path = self.destination_path
        if isinstance(dir_path, str):
            dir_path = dir_path.encode('utf-8')
        objects = self.dirloader.list_objs(
            dir_path=dir_path,
            revision=self.revision,
            release=self.release,
            branch_name=b'master')

        # then
        self.assertEqual(len(objects), 5,
                         "5 obj types: con, dir, rev, rel, snap")
        self.assertEqual(len(objects['content']), 8,
                         "8 contents: 3 files + 5 links")
        self.assertEqual(len(objects['directory']), 6,
                         "6 directories: 5 subdirs + 1 empty")
        self.assertEqual(len(objects['revision']), 1, "synthetic revision")
        self.assertEqual(len(objects['release']), 1, "synthetic release")
        self.assertEqual(len(objects['snapshot']), 1, "snapshot")


TEST_CONFIG = {
    'extraction_dir': '/tmp/tests/loader-tar/',  # where to extract the tarball
    'storage': {  # we instantiate it but we don't use it in test context
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:9999',  # somewhere that does not exist
        }
    },
    'send_contents': False,
    'send_directories': False,
    'send_revisions': False,
    'send_releases': False,
    'send_snapshot': False,
    'content_packet_size': 100,
    'content_packet_block_size_bytes': 104857600,
    'content_packet_size_bytes': 1073741824,
    'directory_packet_size': 250,
    'revision_packet_size': 100,
    'release_packet_size': 100,
}


def parse_config_file(base_filename=None, config_filename=None,
                      additional_configs=None, global_config=True):
    return TEST_CONFIG


# Inhibit side-effect loading configuration from disk
DirLoader.parse_config_file = parse_config_file


class SWHDirLoaderITTest(BaseDirLoaderTest):
    def setUp(self):
        super().setUp()
        self.loader = DirLoaderNoStorage()

    def test_load(self):
        """Process a new tarball should be ok

        """
        # given
        origin = {
            'url': 'file:///tmp/sample-folder',
            'type': 'dir'
        }

        visit_date = 'Tue, 3 May 2016 17:16:32 +0200'

        import datetime
        commit_time = int(datetime.datetime.now(
            tz=datetime.timezone.utc).timestamp()
        )

        swh_person = {
            'name': 'Software Heritage',
            'fullname': 'Software Heritage',
            'email': 'robot@softwareheritage.org'
        }

        revision_message = 'swh-loader-dir: synthetic revision message'
        revision_type = 'tar'
        revision = {
            'date': {
                'timestamp': commit_time,
                'offset': 0,
            },
            'committer_date': {
                'timestamp': commit_time,
                'offset': 0,
            },
            'author': swh_person,
            'committer': swh_person,
            'type': revision_type,
            'message': revision_message,
            'metadata': {},
            'synthetic': True,
        }

        branch = os.path.basename(self.destination_path)

        # when
        self.loader.load(
            dir_path=self.destination_path, origin=origin,
            visit_date=visit_date, revision=revision,
            release=None, branch_name=branch)

        # then
        self.assertCountContents(8)
        self.assertCountDirectories(6)
        self.assertCountRevisions(1)

        actual_revision = self.state('revision')[0]
        self.assertEqual(actual_revision['synthetic'], True)
        self.assertEqual(actual_revision['parents'], [])
        self.assertEqual(actual_revision['type'], 'tar')
        self.assertEqual(actual_revision['message'],
                         b'swh-loader-dir: synthetic revision message')

        self.assertCountReleases(0)
        self.assertCountSnapshots(1)
