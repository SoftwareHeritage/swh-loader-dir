# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import click
import os
import uuid

from swh.loader.core import loader
from swh.model.identifiers import (release_identifier, revision_identifier,
                                   identifier_to_bytes)
from swh.model.from_disk import Directory

from . import converters


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
            full_rev['id'] = identifier_to_bytes(revision_identifier(full_rev))
            return full_rev

        def _release_from(revision_hash, release):
            full_rel = dict(release)
            full_rel['target'] = revision_hash
            full_rel['target_type'] = 'revision'
            full_rel = converters.annotated_tag_to_release(full_rel)
            full_rel['id'] = identifier_to_bytes(release_identifier(full_rel))
            return full_rel

        log_id = str(uuid.uuid4())
        sdir_path = dir_path.decode('utf-8')

        self.log.info("Started listing %s" % dir_path, extra={
            'swh_type': 'dir_list_objs_start',
            'o': sdir_path,
            'swh_id': log_id,
        })

        directory = Directory.from_disk(path=dir_path)

        objects = directory.collect()

        tree_hash = directory.hash
        full_rev = _revision_from(tree_hash, revision)

        objects['revision'] = {full_rev['id']: full_rev}
        objects['release'] = {}

        if release and 'name' in release:
            full_rel = _release_from(full_rev['id'], release)
            objects['release'][full_rel['id']] = release

        self.log.info("Done listing the objects in %s: %d contents, "
                      "%d directories, %d revisions, %d releases" % (
                          sdir_path,
                          len(objects['content']),
                          len(objects['directory']),
                          len(objects['revision']),
                          len(objects['release'])
                      ), extra={
                          'swh_type': 'dir_list_objs_end',
                          'swh_repo': sdir_path,
                          'swh_num_blobs': len(objects['content']),
                          'swh_num_trees': len(objects['directory']),
                          'swh_num_commits': len(objects['revision']),
                          'swh_num_releases': len(objects['release']),
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
            self.dir_path = os.fsencode(self.dir_path)

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
            occs = {}
            for i, occurrence in enumerate(occurrences):
                occs[i] = _occurrence_from(origin_id,
                                           visit,
                                           revision_hash,
                                           occurrence)

            return occs

        # to load the repository, walk all objects, compute their hashes
        self.objects = self.list_repo_objs(
            self.dir_path, self.revision, self.release)

        [rev_id] = self.objects['revision'].keys()

        # Update objects with release and occurrences
        self.objects['occurrence'] = _occurrences_from(
            self.origin_id, self.visit, rev_id, self.occs)

    def store_data(self):
        objects = self.objects
        self.maybe_load_contents(objects['content'].values())
        self.maybe_load_directories(objects['directory'].values())
        self.maybe_load_revisions(objects['revision'].values())
        self.maybe_load_releases(objects['release'].values())
        self.maybe_load_occurrences(objects['occurrence'].values())


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
