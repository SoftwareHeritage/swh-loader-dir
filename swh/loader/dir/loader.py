# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import sys
import uuid

from swh.loader.core import loader, converters
from swh.model import git
from swh.model.git import GitType


class DirLoader(loader.SWHLoader):
    """A bulk loader for a directory.

    This will load the content of the directory.

    """
    def __init__(self,
                 config,
                 origin_id,
                 logging_class='swh.loader.dir.DirLoader'):
        super().__init__(config, origin_id, logging_class)

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
        def get_objects_per_object_type(objects_per_path):
            m = {
                GitType.BLOB: [],
                GitType.TREE: [],
                GitType.COMM: [],
                GitType.RELE: []
            }
            for tree_path in objects_per_path:
                objs = objects_per_path[tree_path]
                for obj in objs:
                    m[obj['type']].append(obj)

            return m

        def _revision_from(tree_hash, revision, objects):
            full_rev = dict(revision)
            full_rev['directory'] = tree_hash
            full_rev = converters.commit_to_revision(full_rev, objects)
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

        objects_per_path = git.walk_and_compute_sha1_from_directory(dir_path)

        objects = get_objects_per_object_type(objects_per_path)

        tree_hash = objects_per_path[git.ROOT_TREE_KEY][0]['sha1_git']

        full_rev = _revision_from(tree_hash, revision, objects_per_path)

        objects[GitType.COMM] = [full_rev]

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

        return objects, objects_per_path

    def process(self, dir_path, origin, revision, release, occurrences):
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
        def _occurrence_from(origin_id, revision_hash, occurrence):
            occ = dict(occurrence)
            occ.update({
                'target': revision_hash,
                'target_type': 'revision',
                'origin': origin_id,
            })
            return occ

        def _occurrences_from(origin_id, revision_hash, occurrences):
            occs = []
            for occurrence in occurrences:
                occs.append(_occurrence_from(origin_id,
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
        objects, objects_per_path = self.list_repo_objs(dir_path, revision,
                                                        release)

        full_rev = objects[GitType.COMM][0]  # only 1 revision

        # Update objects with release and occurrences
        objects[GitType.RELE] = [full_rev]
        objects[GitType.REFS] = _occurrences_from(origin['id'],
                                                  full_rev['id'],
                                                  occurrences)

        self.load(objects, objects_per_path)
        self.flush()

        return {'status': True, 'objects': objects}
