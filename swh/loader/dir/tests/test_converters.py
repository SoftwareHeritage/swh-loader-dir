# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest
import datetime

from nose.tools import istest

from swh.loader.dir import converters
from swh.loader.dir.git import git
from swh.loader.dir.git.git import GitType, GitPerm


class TestConverters(unittest.TestCase):
    @istest
    def format_to_minutes(self):
        self.assertEquals(converters.format_to_minutes('+0100'), 60)
        self.assertEquals(converters.format_to_minutes('-0200'), -120)
        self.assertEquals(converters.format_to_minutes('+1250'), 12*60+50)
        self.assertEquals(converters.format_to_minutes('+0000'), 0)
        self.assertEquals(converters.format_to_minutes('-0000'), 0)

    @istest
    def annotated_tag_to_release(self):
        # given
        release = {
            'sha1_git': '123',
            'revision': '456',
            'name': 'some-release',
            'comment': 'some-comment-on-release',
            'date': 1444054085,
            'offset': '-0300',
            'author_name': 'someone',
            'author_email': 'someone@whatelse.eu'
        }

        expected_release = {
            'id': '123',
            'revision': '456',
            'name': 'some-release',
            'comment': 'some-comment-on-release',
            'date': datetime.datetime.fromtimestamp(
                1444054085,
                tz=datetime.timezone.utc),
            'date_offset': -180,
            'author_name': 'someone',
            'author_email': 'someone@whatelse.eu',
            'synthetic': True,
        }

        # when
        actual_release = converters.annotated_tag_to_release(release)

        # then
        self.assertDictEqual(actual_release, expected_release)

    @istest
    def _blob_to_content_visible(self):
        obj = {
            'length': 9,
            'data': b'some-data',
            'sha1': b'sha1',
            'sha1_git': b'sha1-git',
            'sha256': b'sha256',
            'perms': GitPerm.BLOB,
            'type': GitType.BLOB
        }

        expected_content = {
            'length': 9,
            'data': b'some-data',
            'sha1': b'sha1',
            'sha1_git': b'sha1-git',
            'sha256': b'sha256',
            'perms': GitPerm.BLOB.value,
            'type': GitType.BLOB.value,
            'status': 'visible'
        }

        # when
        actual_content = converters._blob_to_content(obj)

        # then
        self.assertEqual(actual_content, expected_content)

    @istest
    def _blob_to_content_absent(self):
        obj = {
            'length': 9,
            'data': b'some-data',
            'sha1': b'sha1',
            'sha1_git': b'sha1-git',
            'sha256': b'sha256',
            'perms': GitPerm.BLOB,
            'type': GitType.BLOB
        }

        expected_content = {
            'length': 9,
            'data': b'some-data',
            'sha1': b'sha1',
            'sha1_git': b'sha1-git',
            'sha256': b'sha256',
            'perms': GitPerm.BLOB.value,
            'type': GitType.BLOB.value,
            'status': 'absent',
            'reason': 'Content too large',
            'origin': 3}

        # when
        actual_content = converters._blob_to_content(obj,
                                                     max_content_size=5,
                                                     origin_id=3)

        # then
        self.assertDictEqual(actual_content, expected_content)

    @istest
    def tree_to_directory_no_entries(self):
        # given
        tree = {
            'path': 'foo',
            'sha1_git': b'tree_sha1_git'
        }
        objects = {
            'foo': [{'type': GitType.TREE,
                     'perms': GitPerm.TREE,
                     'name': 'bar',
                     'sha1_git': b'sha1-target'},
                    {'type': GitType.BLOB,
                     'perms': GitPerm.BLOB,
                     'name': 'file-foo',
                     'sha1_git': b'file-foo-sha1-target'}]
        }

        expected_directory = {
            'id': b'tree_sha1_git',
            'entries': [{'type': 'dir',
                         'perms': int(GitPerm.TREE.value),
                         'name': 'bar',
                         'target': b'sha1-target'},
                        {'type': 'file',
                         'perms': int(GitPerm.BLOB.value),
                         'name': 'file-foo',
                         'target': b'file-foo-sha1-target'}]
        }

        # when
        actual_directory = converters.tree_to_directory(tree, objects)

        # then
        self.assertEqual(actual_directory, expected_directory)

    @istest
    def commit_to_revision(self):
        # given
        commit = {
            'sha1_git': 'commit-git-sha1',
            'author_date': 1444054085,
            'author_offset': '+0000',
            'committer_date': 1444054085,
            'committer_offset': '-0000',
            'type': 'tar',
            'message': 'synthetic-message-input',
            'author_name': 'author-name',
            'author_email': 'author-email',
            'committer_name': 'committer-name',
            'committer_email': 'committer-email',
            'directory': 'targeted-tree-sha1',
        }

        objects = {
            git.ROOT_TREE_KEY: [{'sha1_git': 'targeted-tree-sha1'}]
        }

        expected_revision = {
            'id': 'commit-git-sha1',
            'date': datetime.datetime.fromtimestamp(
                1444054085,
                tz=datetime.timezone.utc),
            'date_offset': 0,
            'committer_date': datetime.datetime.fromtimestamp(
                1444054085,
                tz=datetime.timezone.utc),
            'committer_date_offset': 0,
            'type': 'tar',
            'directory': 'targeted-tree-sha1',
            'message': 'synthetic-message-input',
            'author_name': 'author-name',
            'author_email': 'author-email',
            'committer_name': 'committer-name',
            'committer_email': 'committer-email',
            'synthetic': True,
            'parents': [],
        }

        # when
        actual_revision = converters.commit_to_revision(commit, objects)

        # then
        self.assertEquals(actual_revision, expected_revision)
