# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import shutil
import subprocess
import tempfile
import unittest

from nose.tools import istest

from swh.loader.dir.loader import DirLoader
from swh.model.git import GitType


class TestLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.tmp_root_path = tempfile.mkdtemp().encode('utf-8')

        start_path = os.path.dirname(__file__).encode('utf-8')
        sample_folder_archive = os.path.join(start_path,
                                             b'../../../../..',
                                             b'swh-storage-testdata',
                                             b'dir-folders',
                                             b'sample-folder.tgz')

        cls.root_path = os.path.join(cls.tmp_root_path, b'sample-folder')

        # uncompress the sample folder
        subprocess.check_output(
            ['tar', 'xvf', sample_folder_archive, '-C', cls.tmp_root_path],
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(cls.tmp_root_path)

    def setUp(self):
        super().setUp()

        self.info = {
            'storage': {
                'cls': 'remote',
                'args': {
                    'url': 'http://localhost:5000/',
                }
            },
            'content_size_limit': 104857600,
            'log_db': 'dbname=softwareheritage-log',
            'directory_packet_size': 25000,
            'content_packet_size': 10000,
            'send_contents': True,
            'send_directories': True,
            'content_packet_size_bytes': 1073741824,
            'occurrence_packet_size': 100000,
            'send_revisions': True,
            'revision_packet_size': 100000,
            'content_packet_block_size_bytes': 104857600,
            'send_occurrences': True,
            'release_packet_size': 100000,
            'send_releases': True
        }

        self.origin = {
            'url': 'file:///dev/null',
            'type': 'dir',
        }

        self.occurrence = {
            'branch': 'master',
            'authority_id': 1,
            'validity': '2015-01-01 00:00:00+00',
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

        self.dirloader = DirLoader(config=self.info)

    @istest
    def load_without_storage(self):
        # when
        objects = self.dirloader.list_repo_objs(
            self.root_path,
            self.revision,
            self.release)

        # then
        self.assertEquals(len(objects), 4,
                          "4 objects types, blob, tree, revision, release")
        self.assertEquals(len(objects[GitType.BLOB]), 8,
                          "8 contents: 3 files + 5 links")
        self.assertEquals(len(objects[GitType.TREE]), 5,
                          "5 directories: 4 subdirs + 1 empty + 1 main dir")
        self.assertEquals(len(objects[GitType.COMM]), 1, "synthetic revision")
        self.assertEquals(len(objects[GitType.RELE]), 1, "synthetic release")

        # print('objects: %s\n objects-per-path: %s\n' %
        #       (objects.keys(),
        #        objects_per_path.keys()))
