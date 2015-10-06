#!/usr/bin/env python3

import os
import shutil
import tempfile

from swh.loader.dir.git import git, utils


def write_file(file, content):
    """Write some content in a file.

    """
    with open(file, 'w') as f:
        f.write(content)


# prepare some arborescence with dirs and files to walk it
# scratch_folder_root = tempfile.mktemp(prefix='swh.loader.dir', suffix='.tmp', dir='/tmp')
scratch_folder_root = os.path.join(os.environ['HOME'], 'tmp')

# scratch_folder_foo = os.path.join(scratch_folder_root, 'foo')
# os.makedirs(scratch_folder_foo, exist_ok=True)
# scratch_folder_bar = os.path.join(scratch_folder_root, 'bar/barfoo')
# os.makedirs(scratch_folder_bar, exist_ok=True)

# scratch_file = os.path.join(scratch_folder_foo, 'quotes.md')
# write_file(scratch_file,
#            'Shoot for the moon. Even if you miss, you\'ll land among the stars.')

# scratch_file2 = os.path.join(scratch_folder_bar, 'another-quote.org')
# write_file(scratch_file2,
#            'A Victory without danger is a triumph without glory.\n-- Pierre Corneille')

def git_ls_tree_rec(hashes):
    """Display the computed result for debug purposes.

    """
    for entry in hashes.keys():
        entry_properties = hashes[entry]
        print("entry name: %s" % entry)
        for file in entry_properties:
            sha1 = utils.hash_to_hex(file['sha1_git'])
            print("%s %s %s\t%s" % (file['perms'].value.decode('utf-8'),
                                    file['type'].value.decode('utf-8'),
                                    sha1,
                                    file['name'].decode('utf-8')))
        print()


hashes = git.walk_and_compute_sha1_from_directory(scratch_folder_root)
git_ls_tree_rec(hashes)

ADDITIONAL_INFO = {
    'revision_author_name': 'swh author',
    'revision_author_email': 'swh@inria.fr',
    'revision_author_date': '1444054085',
    'revision_author_offset': '+0200',
    'revision_committer_name': 'swh committer',
    'revision_committer_email': 'swh@inria.fr',
    'revision_committer_date': '1444054085',
    'revision_committer_offset': '+0200',
    'revision_type': 'dir',
    'revision_message': 'synthetic revision message'
}

revision_hash = git.compute_revision_hash(hashes, ADDITIONAL_INFO)
print('revision directory: %s' % revision_hash)

# clean up
# shutil.rmtree(scratch_folder_root, ignore_errors = True)
