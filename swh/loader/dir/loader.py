# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import click
import os
import sys
import uuid

from swh.loader.core import loader
from swh.model import git

from . import converters


BLOB = b'blob'
TREE = b'tree'
EXEC = b'exec'
LINK = b'link'
COMM = b'commit'
RELE = b'release'
REFS = b'ref'


class DirLoader(loader.SWHLoader):
    """A bulk loader for a directory.

    This will load the content of the directory.

    Args:
        dir_path: source of the directory to import
        origin (dict): dictionary with the following keys:

            - id: origin's id
            - url: url origin we fetched
            - type: type of the origin

        revision (dict): dictionary with the following keys:

            - author_name: revision's author name
            - author_email: revision's author email
            - author_date: timestamp (e.g. 1444054085)
            - author_offset: date offset e.g. -0220, +0100
            - committer_name: revision's committer name
            - committer_email: revision's committer email
            - committer_date: timestamp
            - committer_offset: date offset e.g. -0220, +0100
            - type: type of revision dir, tar
            - message: synthetic message for the revision

        release (dict): dictionary with the following keys:

            - name: release name
            - date: release timestamp (e.g. 1444054085)
            - offset: release date offset e.g. -0220, +0100
            - author_name: release author's name
            - author_email: release author's email
            - comment: release's comment message

        occurrences (dict): dictionary with the following keys:

            - branch: occurrence's branch name
            - date: validity date (e.g. 2015-01-01 00:00:00+00)

    """
    CONFIG_BASE_FILENAME = 'loader/dir'

    def __init__(self, logging_class='swh.loader.dir.DirLoader',
                 config=None):
        super().__init__(logging_class=logging_class, config=config)

    def list_repo_objs(self, dir_path, revision, release):
        """List all objects from dir_path.

        Args:
            dir_path: the directory to list
            revision: revision dictionary representation
            release: release dictionary representation

        Returns:
            list: lists of oid-s with keys for each object type:

            - CONTENT
            - DIRECTORY

        """
        def _revision_from(tree_hash, revision):
            full_rev = dict(revision)
            full_rev['directory'] = tree_hash
            full_rev = converters.commit_to_revision(full_rev)
            full_rev['id'] = git.compute_revision_sha1_git(full_rev)
            return full_rev

        def _release_from(revision_hash, release):
            full_rel = dict(release)
            full_rel['target'] = revision_hash
            full_rel['target_type'] = 'revision'
            full_rel = converters.annotated_tag_to_release(full_rel)
            full_rel['id'] = git.compute_release_sha1_git(full_rel)
            return full_rel

        log_id = str(uuid.uuid4())
        sdir_path = dir_path.decode('utf-8')

        self.log.info("Started listing %s" % dir_path, extra={
            'swh_type': 'dir_list_objs_start',
            'o': sdir_path,
            'swh_id': log_id,
        })

        from swh.model.from_disk import Directory
        directory = Directory.from_disk(path=dir_path)

        def all_entries_from(directory):
            """Retrieve all entries from the top.

            """
            from swh.model.from_disk import Content, Directory
            files = []
            dirs = []
            for name, child in directory.items():
                if isinstance(child, Content):
                    files.append(directory.child_to_directory_entry(
                        name, child))
                    continue
                elif isinstance(child, Directory):
                    dirs.append(directory.child_to_directory_entry(
                        name, child))
                    subfiles, subdirs = all_entries_from(child)
                    files.extend(subfiles)
                    dirs.extend(subdirs)
                else:
                    raise ValueError('Unknown child')

            return files, dirs

        files, dirs = all_entries_from(directory)

        tree_hash = directory.hash
        full_rev = _revision_from(tree_hash, revision)

        objects = {
            BLOB: files,
            TREE: dirs,
            COMM: [full_rev],
            RELE: []
        }

        if release and 'name' in release:
            full_rel = _release_from(full_rev['id'], release)
            objects[RELE] = [full_rel]

        self.log.info("Done listing the objects in %s: %d contents, "
                      "%d directories, %d revisions, %d releases" % (
                          sdir_path,
                          len(objects[BLOB]),
                          len(objects[TREE]),
                          len(objects[COMM]),
                          len(objects[RELE])
                      ), extra={
                          'swh_type': 'dir_list_objs_end',
                          'swh_repo': sdir_path,
                          'swh_num_blobs': len(objects[BLOB]),
                          'swh_num_trees': len(objects[TREE]),
                          'swh_num_commits': len(objects[COMM]),
                          'swh_num_releases': len(objects[RELE]),
                          'swh_id': log_id,
                      })

        return objects

    def prepare(self, *args, **kwargs):
        self.dir_path, self.origin, self.visit_date, self.revision, self.release, self.occs = args  # noqa

        if not os.path.exists(self.dir_path):
            warn_msg = 'Skipping inexistant directory %s' % self.dir_path
            self.log.error(warn_msg,
                           extra={
                               'swh_type': 'dir_repo_list_refs',
                               'swh_repo': self.dir_path,
                               'swh_num_refs': 0,
                           })
            raise ValueError(warn_msg)

        if isinstance(self.dir_path, str):
            self.dir_path = self.dir_path.encode(sys.getfilesystemencoding())

    def get_origin(self):
        return self.origin  # set in prepare method

    def cleanup(self):
        """Nothing to clean up.

        """
        pass

    def fetch_data(self):
        def _occurrence_from(origin_id, visit, revision_hash, occurrence):
            occ = dict(occurrence)
            occ.update({
                'target': revision_hash,
                'target_type': 'revision',
                'origin': origin_id,
                'visit': visit
            })
            return occ

        def _occurrences_from(origin_id, visit, revision_hash, occurrences):
            occs = []
            for occurrence in occurrences:
                occs.append(_occurrence_from(origin_id,
                                             visit,
                                             revision_hash,
                                             occurrence))

            return occs

        # to load the repository, walk all objects, compute their hashes
        self.objects = self.list_repo_objs(
            self.dir_path, self.revision, self.release)

        full_rev = self.objects[COMM][0]  # only 1 revision

        # Update objects with release and occurrences
        self.objects[REFS] = _occurrences_from(
            self.origin_id, self.visit, full_rev['id'], self.occs)

    def store_data(self):
        objects = self.objects
        self.maybe_load_contents(objects[BLOB])
        self.maybe_load_directories(objects[TREE])
        self.maybe_load_revisions(objects[COMM])
        self.maybe_load_releases(objects[RELE])
        self.maybe_load_occurrences(objects[REFS])


@click.command()
@click.option('--dir-path', required=1, help='Directory path to load')
@click.option('--origin-url', required=1, help='Origin url for that directory')
@click.option('--visit-date', default=None, help='Visit date time override')
def main(dir_path, origin_url, visit_date):
    """Debugging purpose."""
    d = DirLoader()

    origin = {
        'url': origin_url,
        'type': 'dir'
    }

    import datetime
    commit_time = int(datetime.datetime.now(
        tz=datetime.timezone.utc).timestamp()
    )

    swh_person = {
        'name': 'Software Heritage',
        'fullname': 'Software Heritage',
        'email': 'robot@softwareheritage.org'
    }
    revision_message = 'swh-loader-dir: synthetic revision message'
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
    release = None
    occurrence = {
        'branch': os.path.basename(dir_path),
    }
    d.load(dir_path, origin, visit_date, revision, release, [occurrence])


if __name__ == '__main__':
    main()
