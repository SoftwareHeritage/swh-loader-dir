# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import shutil
import tempfile
import unittest

from swh.loader.dir import converters
from swh.model import hashutil


def tmpfile_with_content(fromdir, contentfile):
    """Create a temporary file with content contentfile in directory fromdir.

    """
    tmpfilepath = tempfile.mktemp(
        suffix='.swh',
        prefix='tmp-file-for-test',
        dir=fromdir)

    with open(tmpfilepath, 'wb') as f:
        f.write(contentfile)

    return tmpfilepath


class TestConverters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tmpdir = tempfile.mkdtemp(prefix='test-swh-loader-dir.')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)
        super().tearDownClass()

    def test_format_to_minutes(self):
        self.assertEqual(converters.format_to_minutes('+0100'), 60)
        self.assertEqual(converters.format_to_minutes('-0200'), -120)
        self.assertEqual(converters.format_to_minutes('+1250'), 12*60+50)
        self.assertEqual(converters.format_to_minutes('+0000'), 0)
        self.assertEqual(converters.format_to_minutes('-0000'), 0)

    def test_annotated_tag_to_release(self):
        # given
        release = {
            'name': 'v0.0.1',
            'message': 'synthetic-message-input',
            'author': {'name': 'author-name',
                       'email': 'author-email',
                       'fullname': 'fullname'},
        }

        expected_release = {
            'name': b'v0.0.1',
            'message': b'synthetic-message-input',
            'author': {'name': b'author-name',
                       'email': b'author-email',
                       'fullname': b'fullname'},
            'synthetic': True,
        }

        # when
        actual_release = converters.annotated_tag_to_release(release)

        # then
        self.assertDictEqual(actual_release, expected_release)

    def test_commit_to_revision(self):
        # given
        commit = {
            'sha1_git': 'commit-git-sha1',
            'directory': 'targeted-tree-sha1',
            'date': {'timestamp': 1444054085, 'offset': '+0000'},
            'committer_date': {'timestamp': 1444054085, 'offset': '+0000'},
            'type': 'tar',
            'message': 'synthetic-message-input',
            'author': {'name': 'author-name',
                       'email': 'author-email',
                       'fullname': 'fullname'},
            'committer': {'name': 'author-name',
                          'email': 'author-email',
                          'fullname': 'fullname'},
            'directory': 'targeted-tree-sha1',
        }

        expected_revision = {
            'sha1_git': 'commit-git-sha1',
            'directory': 'targeted-tree-sha1',
            'date': {'timestamp': 1444054085, 'offset': '+0000'},
            'committer_date': {'timestamp': 1444054085, 'offset': '+0000'},
            'type': 'tar',
            'message': b'synthetic-message-input',
            'author': {'name': b'author-name',
                       'email': b'author-email',
                       'fullname': b'fullname'},
            'committer': {'name': b'author-name',
                          'email': b'author-email',
                          'fullname': b'fullname'},
            'directory': 'targeted-tree-sha1',
            'synthetic': True,
            'parents': []
        }

        # when
        actual_revision = converters.commit_to_revision(commit)

        # then
        self.assertEqual(actual_revision, expected_revision)

    def test_commit_to_revision_with_parents(self):
        """Commit with existing parents should not lose information

        """
        h = '10041ddb6cbc154c24227b1e8759b81dcd99ea3e'

        # given
        commit = {
            'sha1_git': 'commit-git-sha1',
            'directory': 'targeted-tree-sha1',
            'date': {'timestamp': 1444054085, 'offset': '+0000'},
            'committer_date': {'timestamp': 1444054085, 'offset': '+0000'},
            'type': 'tar',
            'message': 'synthetic-message-input',
            'author': {'name': 'author-name',
                       'email': 'author-email',
                       'fullname': 'fullname'},
            'committer': {'name': 'author-name',
                          'email': 'author-email',
                          'fullname': 'fullname'},
            'directory': 'targeted-tree-sha1',
            'parents': [h],
        }

        expected_revision = {
            'sha1_git': 'commit-git-sha1',
            'directory': 'targeted-tree-sha1',
            'date': {'timestamp': 1444054085, 'offset': '+0000'},
            'committer_date': {'timestamp': 1444054085, 'offset': '+0000'},
            'type': 'tar',
            'message': b'synthetic-message-input',
            'author': {'name': b'author-name',
                       'email': b'author-email',
                       'fullname': b'fullname'},
            'committer': {'name': b'author-name',
                          'email': b'author-email',
                          'fullname': b'fullname'},
            'directory': 'targeted-tree-sha1',
            'synthetic': True,
            'parents': [hashutil.hash_to_bytes(h)]
        }

        # when
        actual_revision = converters.commit_to_revision(commit)

        # then
        self.assertEqual(actual_revision, expected_revision)
