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

from swh.loader.dir.loader import DirLoader, BLOB, TREE, COMM, RELE


class InitTestLoader(unittest.TestCase):
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

        cls.root_path = os.path.join(cls.tmp_root_path)

        # uncompress the sample folder
        subprocess.check_output(
            ['tar', 'xvf', sample_folder_archive, '-C', cls.tmp_root_path],
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(cls.tmp_root_path)


class DirLoaderListRepoObject(InitTestLoader):

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
        self.assertEquals(len(objects[BLOB]), 8,
                          "8 contents: 3 files + 5 links")
        self.assertEquals(len(objects[TREE]), 5,
                          "5 directories: 4 subdirs + 1 empty")
        self.assertEquals(len(objects[COMM]), 1, "synthetic revision")
        self.assertEquals(len(objects[RELE]), 1, "synthetic release")

        # print('objects: %s\n objects-per-path: %s\n' %
        #       (objects.keys(),
        #        objects_per_path.keys()))


class LoaderNoStorageForTest:
    """Mixin class to inhibit the persistence and keep in memory the data
    sent for storage.

    cf. SWHDirLoaderNoStorage

    """
    def __init__(self):
        super().__init__()
        # Init the state
        self.all_contents = []
        self.all_directories = []
        self.all_revisions = []
        self.all_releases = []
        self.all_occurrences = []

    def send_origin(self, origin):
        self.origin = origin

    def send_origin_visit(self, origin_id, ts):
        self.origin_visit = {
            'origin': origin_id,
            'ts': ts,
            'visit': 1,
        }
        return self.origin_visit

    def update_origin_visit(self, origin_id, visit, status):
        self.status = status
        self.origin_visit = visit

    def maybe_load_contents(self, all_contents):
        self.all_contents.extend(all_contents)

    def maybe_load_directories(self, all_directories):
        self.all_directories.extend(all_directories)

    def maybe_load_revisions(self, all_revisions):
        self.all_revisions.extend(all_revisions)

    def maybe_load_releases(self, releases):
        self.all_releases.extend(releases)

    def maybe_load_occurrences(self, all_occurrences):
        self.all_occurrences.extend(all_occurrences)

    def open_fetch_history(self):
        return 1

    def close_fetch_history_success(self, fetch_history_id):
        pass

    def close_fetch_history_failure(self, fetch_history_id):
        pass


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
    'send_occurrences': False,
    'content_packet_size': 100,
    'content_packet_block_size_bytes': 104857600,
    'content_packet_size_bytes': 1073741824,
    'directory_packet_size': 250,
    'revision_packet_size': 100,
    'release_packet_size': 100,
    'occurrence_packet_size': 100,
}


def parse_config_file(base_filename=None, config_filename=None,
                      additional_configs=None, global_config=True):
    return TEST_CONFIG


# Inhibit side-effect loading configuration from disk
DirLoader.parse_config_file = parse_config_file


class SWHDirLoaderNoStorage(LoaderNoStorageForTest, DirLoader):
    """A DirLoader with no persistence.

    Context:
        Load a tarball with a persistent-less tarball loader

    """
    pass


class SWHDirLoaderITTest(InitTestLoader):
    def setUp(self):
        super().setUp()

        self.loader = SWHDirLoaderNoStorage()

    @istest
    def load(self):
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

        revision_message = 'swh-loader-tar: synthetic revision message'
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

        occurrence = {
            'branch': os.path.basename(self.root_path),
        }

        # when
        self.loader.load(self.root_path, origin, visit_date, revision, None,
                         [occurrence])

        # then
        self.assertEquals(len(self.loader.all_contents), 8)
        self.assertEquals(len(self.loader.all_directories), 5)
        self.assertEquals(len(self.loader.all_revisions), 1)

        actual_revision = self.loader.all_revisions[0]
        self.assertEquals(actual_revision['synthetic'],
                          True)
        self.assertEquals(actual_revision['parents'],
                          [])
        self.assertEquals(actual_revision['type'],
                          'tar')
        self.assertEquals(actual_revision['message'],
                          b'swh-loader-tar: synthetic revision message')

        self.assertEquals(len(self.loader.all_releases), 0)
        self.assertEquals(len(self.loader.all_occurrences), 1)
