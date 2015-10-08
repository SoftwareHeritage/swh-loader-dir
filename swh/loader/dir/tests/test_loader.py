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

from swh.core.hashutil import hex_to_hash
from swh.loader.dir.loader import DirLoader
from swh.loader.dir.git.git import GitType


class TestLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tmp_root_path = tempfile.mkdtemp()

        sample_folder_archive = os.path.join(os.path.dirname(__file__),
                                             '../../../../..',
                                             'swh-storage-testdata',
                                             'dir-folders',
                                             'sample-folder.tgz')

        cls.root_path = os.path.join(cls.tmp_root_path, 'sample-folder')

        # uncompress the sample folder
        subprocess.check_output(
            ['tar', 'xvf', sample_folder_archive, '-C', cls.tmp_root_path],
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(cls.tmp_root_path)
        print(cls.tmp_root_path)

    def setUp(self):
        super().setUp()


        self.info = {
            'storage_class': 'remote_storage',
            'storage_args': ['http://localhost:5000/'],

            # origin information
            'origin_url': 'file:///dev/null',

            # occurrence information
            'branch': 'master',
            'authority_id': 1,
            'validity': '2015-01-01 00:00:00+00',

            # revision information
            'revision_author_name': 'swh author',
            'revision_author_email': 'swh@inria.fr',
            'revision_author_date': '1444054085',
            'revision_author_offset': '+0200',
            'revision_committer_name': 'swh committer',
            'revision_committer_email': 'swh@inria.fr',
            'revision_committer_date': '1444054085',
            'revision_committer_offset': '+0200',
            'revision_type': 'tar',
            'revision_message': 'synthetic revision',

            # release information
            'release_name': 'v0.0.1',
            'release_date': '1444054085',
            'release_offset': '+0200',
            'release_author_name': 'swh author',
            'release_author_email': 'swh@inria.fr',
            'release_comment': 'synthetic release',
        }

        self.dirloader = DirLoader(self.info)

    @istest
    def load_without_storage(self):
        # when
        objects, objects_per_path = self.dirloader.list_repo_objs(self.root_path, self.info)

        # then
        self.assertEquals(len(objects), 4, "4 objects types, blob, tree, revision, release")
        self.assertEquals(len(objects[GitType.BLOB]), 8, "8 contents: 3 files + 5 links")
        self.assertEquals(len(objects[GitType.TREE]), 4, "4 directories: 3 subdir + 1 main dir")
        self.assertEquals(len(objects[GitType.COMM]), 1, "1 synthetic revision")
        self.assertEquals(len(objects[GitType.RELE]), 1, "1 synthetic release")

        self.assertEquals(len(objects_per_path), 5, "4 folders + <root>")

#        print('objects: %s\n objects-per-path: %s\n' % (objects.keys(), objects_per_path.keys()))
