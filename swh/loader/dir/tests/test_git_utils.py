# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.loader.dir.git import utils


class GitUtilsHashlib(unittest.TestCase):

    def setUp(self):
        self.blob_data = b'42\n'

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
            'blob_sha1_git': bytes.fromhex('d81cc0710eb6cf9efd5b920a8453e1'
                                           'e07157b6cd'),
            'tree_sha1_git': bytes.fromhex('ac212302c45eada382b27bfda795db'
                                           '121dacdb1c'),
            'commit_sha1_git': bytes.fromhex('e960570b2e6e2798fa4cfb9af2c399'
                                             'd629189653'),
            'tag_sha1_git': bytes.fromhex('bc2b99ba469987bcf1272c189ed534'
                                          'e9e959f120'),
        }

    @istest
    def unknown_header_type(self):
        with self.assertRaises(ValueError) as cm:
            utils.hashdata(b'any-data', 'some-unknown-type')

        self.assertIn('Only supported types', cm.exception.args[0])

    @istest
    def hashdata_content(self):
        # when
        checksums = utils.hashdata(self.blob_data, 'blob')

        # then
        self.assertEqual(checksums['sha1_git'],
                         self.checksums['blob_sha1_git'])

    @istest
    def hashdata_tree(self):
        # when
        checksums = utils.hashdata(self.tree_data, 'tree')

        # then
        self.assertEqual(checksums['sha1_git'],
                         self.checksums['tree_sha1_git'])

    @istest
    def hashdata_revision(self):
        # when
        checksums = utils.hashdata(self.commit_data, 'commit')

        # then
        self.assertEqual(checksums['sha1_git'],
                         self.checksums['commit_sha1_git'])

    @istest
    def hashdata_tag(self):
        # when
        checksums = utils.hashdata(self.tag_data, 'tag')

        # then
        self.assertEqual(checksums['sha1_git'],
                         self.checksums['tag_sha1_git'])

    @istest
    def to_bytes(self):
        # given
        inputs = ['ha\udcefti.ogg', 'blah-123']
        expected_outputs = [b'ha\xefti.ogg', b'blah-123']

        input_outputs = zip(inputs, expected_outputs)

        # when
        for input, expected_output in input_outputs:
            self.assertEquals(
                utils.to_bytes(input),
                expected_output,
                'For %s, should have been %s' % (input, expected_output))
