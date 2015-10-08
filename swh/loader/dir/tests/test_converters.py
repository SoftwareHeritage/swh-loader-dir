# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest
from datetime import datetime

from swh.loader.dir import converters
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
    def origin_url_to_origin(self):
        # given
        origin_url = 'foobar'

        # when
        self.assertDictEqual({
            'type': 'dir',
            'url': origin_url,
        }, converters.origin_url_to_origin(origin_url))

    @istest
    def annotated_tag_to_release(self):
        # given
        release = {
            'sha1_git': '123',
            'revision_sha1_git': '456',
            'release_name': 'some-release',
            'release_comment': 'some-comment-on-release',
            'release_date': 1444054085,
            'release_offset': '-0300',
            'release_author_name': 'someone',
            'release_author_email': 'someone@whatelse.eu'
        }

        expected_release = {
            'id': '123',
            'revision': '456',
            'name': 'some-release',
            'comment': 'some-comment-on-release',
            'date': datetime.fromtimestamp(1444054085),
            'date_offset': -180,
            'author_name': 'someone',
            'author_email': 'someone@whatelse.eu',
        }

        # when
        actual_release = converters.annotated_tag_to_release(release)

        # then
        self.assertDictEqual(
            expected_release,
            actual_release)

    @istest
    def blob_to_content_visible(self):
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
        actual_content = converters.blob_to_content(obj)

        # then
        self.assertEqual(expected_content, actual_content)

    @istest
    def blob_to_content_absent(self):
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
        actual_content = converters.blob_to_content(obj,
                                                    max_content_size=5,
                                                    origin_id=3)

        # then
        self.assertEqual(expected_content, actual_content)

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
            'revision_author_date': 1444054085,
            'revision_author_offset': '+0000',
            'revision_committer_date': 1444054085,
            'revision_committer_offset': '-0000',
            'revision_type': 'tar',
            'revision_message': 'synthetic-message-input',
            'revision_author_name': 'author-name',
            'revision_author_email': 'author-email',
            'revision_committer_name': 'committer-name',
            'revision_committer_email': 'committer-email',
        }

        objects = {
            '<root>': [{'sha1_git': 'targeted-tree-sha1'}]
        }

        expected_revision = {
            'id': 'commit-git-sha1',
            'date': datetime.fromtimestamp(1444054085),
            'date_offset': 0,
            'committer_date': datetime.fromtimestamp(1444054085),
            'committer_date_offset': 0,
            'type': 'tar',
            'directory': 'targeted-tree-sha1',
            'message': 'synthetic-message-input',
            'author_name': 'author-name',
            'author_email': 'author-email',
            'committer_name': 'committer-name',
            'committer_email': 'committer-email',
            'parents': [],
        }

        # when
        actual_revision = converters.commit_to_revision(commit, objects)

        # then
        self.assertEquals(actual_revision, expected_revision)
