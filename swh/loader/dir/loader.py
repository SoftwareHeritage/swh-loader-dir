# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
import os
import sys
import uuid

from swh.loader.core import loader
from swh.model import git
from swh.model.git import GitType

from . import converters


class DirLoader(loader.SWHLoader):
    """A bulk loader for a directory.

    This will load the content of the directory.

    """
    CONFIG_BASE_FILENAME = 'loader/dir.ini'

    def __init__(self, logging_class='swh.loader.dir.DirLoader',
                 config=None):
        super().__init__(logging_class=logging_class, config=config)

    def list_repo_objs(self, dir_path, revision, release):
        """List all objects from dir_path.

        Args:
            - dir_path (path): the directory to list
            - revision: revision dictionary representation
            - release: release dictionary representation

        Returns:
            a dict containing lists of `Oid`s with keys for each object type:
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
            'swh_repo': sdir_path,
            'swh_id': log_id,
        })

        objects_per_path = git.compute_hashes_from_directory(dir_path)

        tree_hash = objects_per_path[dir_path]['checksums']['sha1_git']
        full_rev = _revision_from(tree_hash, revision)

        objects = {
            GitType.BLOB: list(
                git.objects_per_type(GitType.BLOB, objects_per_path)),
            GitType.TREE: list(
                git.objects_per_type(GitType.TREE, objects_per_path)),
            GitType.COMM: [full_rev],
            GitType.RELE: []
        }

        if release and 'name' in release:
            full_rel = _release_from(full_rev['id'], release)
            objects[GitType.RELE] = [full_rel]

        self.log.info("Done listing the objects in %s: %d contents, "
                      "%d directories, %d revisions, %d releases" % (
                          sdir_path,
                          len(objects[GitType.BLOB]),
                          len(objects[GitType.TREE]),
                          len(objects[GitType.COMM]),
                          len(objects[GitType.RELE])
                      ), extra={
                          'swh_type': 'dir_list_objs_end',
                          'swh_repo': sdir_path,
                          'swh_num_blobs': len(objects[GitType.BLOB]),
                          'swh_num_trees': len(objects[GitType.TREE]),
                          'swh_num_commits': len(objects[GitType.COMM]),
                          'swh_num_releases': len(objects[GitType.RELE]),
                          'swh_id': log_id,
                      })

        return objects

    def load(self, dir_path, origin, visit, revision, release, occurrences):
        """Load a directory in backend.

        Args:
            - dir_path: source of the directory to import
            - origin: Dictionary origin
              - id: origin's id
              - url: url origin we fetched
              - type: type of the origin
            - revision: Dictionary of information needed, keys are:
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
            - release: Dictionary of information needed, keys are:
              - name: release name
              - date: release timestamp (e.g. 1444054085)
              - offset: release date offset e.g. -0220, +0100
              - author_name: release author's name
              - author_email: release author's email
              - comment: release's comment message
            - occurrences: List of occurrences as dictionary.
              Information needed, keys are:
              - branch: occurrence's branch name
              - date: validity date (e.g. 2015-01-01 00:00:00+00)

        Returns:
            Dictionary with the following keys:
            - status: mandatory, the status result as a boolean
            - stderr: optional when status is True, mandatory otherwise
            - objects: the actual objects sent to swh storage

        """
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

        if not os.path.exists(dir_path):
            warn_msg = 'Skipping inexistant directory %s' % dir_path
            self.log.warn(warn_msg,
                          extra={
                              'swh_type': 'dir_repo_list_refs',
                              'swh_repo': dir_path,
                              'swh_num_refs': 0,
                          })
            return {'status': False, 'stderr': warn_msg}

        if isinstance(dir_path, str):
            dir_path = dir_path.encode(sys.getfilesystemencoding())

        # to load the repository, walk all objects, compute their hash
        objects = self.list_repo_objs(dir_path, revision, release)

        full_rev = objects[GitType.COMM][0]  # only 1 revision

        # Update objects with release and occurrences
        objects[GitType.REFS] = _occurrences_from(
            origin['id'], visit, full_rev['id'], occurrences)

        # load contents
        self.maybe_load_contents(objects[GitType.BLOB])
        self.maybe_load_directories(objects[GitType.TREE])
        self.maybe_load_revisions(objects[GitType.COMM])
        self.maybe_load_releases(objects[GitType.RELE])
        self.maybe_load_occurrences(objects[GitType.REFS])

        self.flush()

        return {'status': True, 'objects': objects}

    def prepare_and_load(self, dir_path, origin, revision, release,
                         occurrences):
        """First prepare the origin, origin_visit.
        Then load the data in storage.
        At last, close the origin_visit.

        """
        self.origin_id = self.storage.origin_add_one(origin)
        origin['id'] = self.origin_id

        fetch_history_id = self.open_fetch_history()
        date_visit = datetime.datetime.now(tz=datetime.timezone.utc)
        origin_visit = self.storage.origin_visit_add(origin['id'], date_visit)
        visit = origin_visit['visit']

        try:
            self.load(dir_path, origin, visit, revision, release, occurrences)
            self.close_fetch_history_success(fetch_history_id)
            self.storage.origin_visit_update(
                self.origin_id, visit, status='full')
        except:
            self.close_fetch_history_failure(fetch_history_id)
            self.storage.origin_visit_update(
                self.origin_id, visit, status='partial')
            raise
