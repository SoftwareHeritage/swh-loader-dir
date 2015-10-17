# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.loader.dir import producer


class TestProducer(unittest.TestCase):
    @istest
    def is_archive(self):
        # given
        file_tryouts = [
            'free-ipmi-1.2.2.tar',
            'free-ipmi-1.2.2.tar.gz',
            'free-ipmi-1.2.2.tar.tgz',
            'gcc-testsuite-4.4.2-4.4.3.diff.bz2',
            'gcc-java-4.0.4.tar.gz',
            'gmp-2.0.tar.lzma',
            'win-gerwin-0.6.zip',
            'ballandpaddle-0.8.0.tar.xz',
            'mail-1.1.1.some.lz',
            'gmp-4.1.1-4.1.2.diff.tar.blah.foo.bar.Z',
            'findutils-4.2.18.tar.bzip2'
        ]

        # then
        for f in file_tryouts:
            res = producer.is_archive(f)
            self.assertTrue(res,
                            '%s should be identified as archive' % f)

    @istest
    def is_archive_not(self):
        # given
        file_tryouts = [
            'free-ipmi-1.2.2.gz.sig',
            'free-ipmi-1.2.2.bz3',
            'free-ipmi-1.2.2.blah',
            'free-ipmi-1.2.2.other',
            'free-ipmi-1.2.2.md5',
            'free-ipmi-1.2.2.rpm',
            'free-ipmi-1.2.2.dpkg',
            'free-ipmi-1.2.2.deb',
            'free-ipmi-1.2.2.7z',
            'free-ipmi-1.2.2.foobar',
            'apl_1.3-1_i386.deb.sig'
        ]

        # then
        for f in file_tryouts:
            self.assertFalse(
                producer.is_archive(f),
                '%s should not be identified as archive' % f)

    @istest
    def compute_basic_release_number(self):
        files = {
            'free-ipmi-1.2.2.tar': '1.2.2',
            'free-ipmi-1.2.2.tar.gz': '1.2.2',
            'free-ipmi-1.2.2.tar.tgz': '1.2.2',
            'gcc-testsuite-4.4.2-4.4.3.diff.bz2': '4.4.2-4.4.3.diff',
            'gcc-java-4.0.4.tar.gz': '4.0.4',
            'gmp-2.0.tar.lzma': '2.0',
            'win-gerwin-0.6.zip': '0.6',
            'ballandpaddle-0.8.0.tar.xz': '0.8.0',
            'mail-1.1.1.some.lz': '1.1.1.some',
            'gmp-4.1.1-4.1.2.diff.tar.Z': '4.1.1-4.1.2.diff',
            'findutils-4.2.18.tar.bzip2': '4.2.18',
            'greg-1.4.tar.gz': '1.4',

            # . separator
            'greg.1.4.tar.gz': '1.4',

            # number in software product
            'aspell6-pt_BR-20070411-0.tar.bz2': '20070411-0',
            'libosip2-3.3.0.tar.gz': '3.3.0',

            # particular patterns...
            'gift-0.1.9+3epsilon.tar.gz': '0.1.9+3epsilon',
            'gift-0.1.6pre2.tgz': '0.1.6pre2',
            'binutils-2.19.1a.tar.bz2': '2.19.1a',
            'readline-4.2-4.2a.diff.gz': '4.2-4.2a.diff',

            # with arch patterns
            'cvs-1.12.6-BSD.bin.gz': '1.12.6-BSD.bin',
            'cvs-1.12.12-SunOS-5.8-i386.gz': '1.12.12-SunOS-5.8-i386',
            'gnutls-3.0.20-w32.zip': '3.0.20-w32',
            'mit-scheme_7.7.90+20080130-0gutsy1.diff.gz':
            '7.7.90+20080130-0gutsy1.diff',

            # no release number
            'gnu.ps.gz': None,
            'direvent-latest.tar.gz': None,
        }

        # then
        for f in files.keys():
            rel_num = producer.release_number(f)
            self.assertEquals(
                files[f],
                rel_num,
                'for %s, the version should be %s' % (f, files[f]))
