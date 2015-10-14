# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.loader.dir.git import git
from swh.loader.dir.git.git import GitPerm, GitType


class GitHashlib(unittest.TestCase):
    def setUp(self):
        self.tree_data = b''.join([b'40000 barfoo\0',
                                   bytes.fromhex('c3020f6bf135a38c6df'
                                                 '3afeb5fb38232c5e07087'),
                                   b'100644 blah\0',
                                   bytes.fromhex('63756ef0df5e4f10b6efa'
                                                 '33cfe5c758749615f20'),
                                   b'100644 hello\0',
                                   bytes.fromhex('907b308167f0880fb2a'
                                                 '5c0e1614bb0c7620f9dc3')])

        self.commit_data = """tree 1c61f7259dcb770f46b194d941df4f08ff0a3970
author Antoine R. Dumont (@ardumont) <antoine.romain.dumont@gmail.com> 1444054085 +0200
committer Antoine R. Dumont (@ardumont) <antoine.romain.dumont@gmail.com> 1444054085 +0200

initial
""".encode('utf-8')  # NOQA
        self.tag_data = """object 24d012aaec0bc5a4d2f62c56399053d6cc72a241
type commit
tag 0.0.1
tagger Antoine R. Dumont (@ardumont) <antoine.romain.dumont@gmail.com> 1444225145 +0200

blah
""".encode('utf-8')  # NOQA

        self.checksums = {
            'tree_sha1_git': bytes.fromhex('ac212302c45eada382b27bfda795db'
                                           '121dacdb1c'),
            'commit_sha1_git': bytes.fromhex('e960570b2e6e2798fa4cfb9af2c399'
                                             'd629189653'),
            'tag_sha1_git': bytes.fromhex('bc2b99ba469987bcf1272c189ed534'
                                          'e9e959f120'),
        }

    @istest
    def compute_directory_git_sha1(self):
        # given
        dirpath = 'some-dir-path'
        hashes = {
            dirpath: [{'perms': GitPerm.TREE,
                       'type': GitType.TREE,
                       'name': b'barfoo',
                       'sha1_git': bytes.fromhex('c3020f6bf135a38c6df'
                                                 '3afeb5fb38232c5e07087')},
                      {'perms': GitPerm.BLOB,
                       'type': GitType.BLOB,
                       'name': b'hello',
                       'sha1_git': bytes.fromhex('907b308167f0880fb2a'
                                                 '5c0e1614bb0c7620f9dc3')},
                      {'perms': GitPerm.BLOB,
                       'type': GitType.BLOB,
                       'name': b'blah',
                       'sha1_git': bytes.fromhex('63756ef0df5e4f10b6efa'
                                                 '33cfe5c758749615f20')}]
        }

        # when
        checksums = git.compute_directory_git_sha1(dirpath, hashes)

        # then
        self.assertEqual(checksums['sha1_git'],
                         self.checksums['tree_sha1_git'])

    @istest
    def compute_revision_git_sha1(self):
        # given
        tree_hash = bytes.fromhex('1c61f7259dcb770f46b194d941df4f08ff0a3970')
        revision = {
            'revision_author_name': 'Antoine R. Dumont (@ardumont)',
            'revision_author_email': 'antoine.romain.dumont@gmail.com',
            'revision_author_date': '1444054085',
            'revision_author_offset': '+0200',
            'revision_committer_name': 'Antoine R. Dumont (@ardumont)',
            'revision_committer_email': 'antoine.romain.dumont@gmail.com',
            'revision_committer_date': '1444054085',
            'revision_committer_offset': '+0200',
            'revision_message': 'initial',
            'revision_type': 'tar'
        }

        # when
        checksums = git.compute_revision_git_sha1(tree_hash, revision)

        # then
        self.assertEqual(checksums['sha1_git'],
                         self.checksums['commit_sha1_git'])
        self.assertDictContainsSubset(revision, checksums)

    @istest
    def compute_release(self):
        # given
        revision_hash = bytes.fromhex('24d012aaec0bc5a4d2f62c56399053'
                                      'd6cc72a241')
        release = {
            'release_name': '0.0.1',
            'release_author_name': 'Antoine R. Dumont (@ardumont)',
            'release_author_email': 'antoine.romain.dumont@gmail.com',
            'release_date': '1444225145',
            'release_offset': '+0200',
            'release_comment': 'blah',
        }

        # when
        checksums = git.compute_release(revision_hash, release)

        # then
        self.assertEqual(checksums['sha1_git'],
                         self.checksums['tag_sha1_git'])
        self.assertDictContainsSubset(release, checksums)
