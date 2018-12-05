# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import pytest

from swh.loader.core.tests import BaseLoaderTest
from swh.loader.dir.loader import DirLoader

from swh.model import hashutil


@pytest.mark.fs
class BaseDirLoaderTest(BaseLoaderTest):
    def setUp(self, archive_name='sample-folder.tgz'):
        super().setUp(archive_name=archive_name,
                      prefix_tmp_folder_name='swh.loader.dir.',
                      start_path=os.path.dirname(__file__))


class DirLoaderNoStorage(DirLoader):
    """A DirLoader with no persistence.

    Context:
        Load a tarball with a persistent-less tarball loader

    """
    def parse_config_file(self, *args, **kwargs):
        return {
            'storage': {
                'cls': 'memory',
                'args': {
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


class DirLoaderListRepoObject(BaseDirLoaderTest):
    def setUp(self):
        super().setUp()

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

        self.dirloader = DirLoaderNoStorage()

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


class SWHDirLoaderITTest(BaseDirLoaderTest):
    def setUp(self):
        super().setUp()
        self.loader = DirLoaderNoStorage()
        self.storage = self.loader.storage

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
        commit_time = int(datetime.datetime(
            2018, 12, 5, 13, 35, 23, 0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=1))
        ).timestamp())

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

        rev_id = hashutil.hash_to_bytes(
            'e974eda2328f6e97bc185307c692a115fe3a7eae')
        actual_revision = next(self.storage.revision_get([rev_id]))
        self.assertEqual(actual_revision['synthetic'], True)
        self.assertEqual(actual_revision['parents'], [])
        self.assertEqual(actual_revision['type'], 'tar')
        self.assertEqual(actual_revision['message'],
                         b'swh-loader-dir: synthetic revision message')

        self.assertCountReleases(0)
        self.assertCountSnapshots(1)
