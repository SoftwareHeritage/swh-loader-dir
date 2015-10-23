# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import os
import psycopg2
import sys
import traceback
import uuid

from retrying import retry

from swh.core import config

from swh.loader.dir import converters
from swh.loader.dir.git import git
from swh.loader.dir.git.git import GitType


def send_in_packets(source_list, formatter, sender, packet_size,
                    packet_size_bytes=None, *args, **kwargs):
    """Send objects from `source_list`, passed through `formatter` (with
    extra args *args, **kwargs), using the `sender`, in packets of
    `packet_size` objects (and of max `packet_size_bytes`).

    """
    formatted_objects = []
    count = 0
    if not packet_size_bytes:
        packet_size_bytes = 0
    for obj in source_list:
        formatted_object = formatter(obj, *args, **kwargs)
        if formatted_object:
            formatted_objects.append(formatted_object)
        else:
            continue
        if packet_size_bytes:
            count += formatted_object['length']
        if len(formatted_objects) >= packet_size or count > packet_size_bytes:
            sender(formatted_objects)
            formatted_objects = []
            count = 0

    if formatted_objects:
        sender(formatted_objects)


def retry_loading(error):
    """Retry policy when the database raises an integrity error"""
    if not isinstance(error, psycopg2.IntegrityError):
        return False

    logger = logging.getLogger('swh.loader.git.DirLoader')

    error_name = error.__module__ + '.' + error.__class__.__name__
    logger.warning('Retry loading a batch', exc_info=False, extra={
        'swh_type': 'storage_retry',
        'swh_exception_type': error_name,
        'swh_exception': traceback.format_exception(
            error.__class__,
            error,
            error.__traceback__,
        ),
    })

    return True


class DirLoader(config.SWHConfig):
    """A bulk loader for a directory"""

    DEFAULT_CONFIG = {
        'storage_class': ('str', 'remote_storage'),
        'storage_args': ('list[str]', ['http://localhost:5000/']),

        'send_contents': ('bool', True),
        'send_directories': ('bool', True),
        'send_revisions': ('bool', True),
        'send_releases': ('bool', True),
        'send_occurrences': ('bool', True),

        'content_packet_size': ('int', 10000),
        'content_packet_size_bytes': ('int', 1024 * 1024 * 1024),
        'directory_packet_size': ('int', 25000),
        'revision_packet_size': ('int', 100000),
        'release_packet_size': ('int', 100000),
        'occurrence_packet_size': ('int', 100000),
    }

    def __init__(self, config):
        self.config = config

        if self.config['storage_class'] == 'remote_storage':
            from swh.storage.api.client import RemoteStorage as Storage
        else:
            from swh.storage import Storage

        self.storage = Storage(*self.config['storage_args'])

        self.log = logging.getLogger('swh.loader.dir.DirLoader')

    @retry(retry_on_exception=retry_loading, stop_max_attempt_number=3)
    def send_contents(self, content_list):
        """Actually send properly formatted contents to the database"""
        num_contents = len(content_list)
        log_id = str(uuid.uuid4())
        self.log.debug("Sending %d contents" % num_contents,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'content',
                           'swh_num': num_contents,
                           'swh_id': log_id,
                       })
        self.storage.content_add(content_list)
        self.log.debug("Done sending %d contents" % num_contents,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'content',
                           'swh_num': num_contents,
                           'swh_id': log_id,
                       })

    @retry(retry_on_exception=retry_loading, stop_max_attempt_number=3)
    def send_directories(self, directory_list):
        """Actually send properly formatted directories to the database"""
        num_directories = len(directory_list)
        log_id = str(uuid.uuid4())
        self.log.debug("Sending %d directories" % num_directories,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'directory',
                           'swh_num': num_directories,
                           'swh_id': log_id,
                       })
        self.storage.directory_add(directory_list)
        self.log.debug("Done sending %d directories" % num_directories,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'directory',
                           'swh_num': num_directories,
                           'swh_id': log_id,
                       })

    @retry(retry_on_exception=retry_loading, stop_max_attempt_number=3)
    def send_revisions(self, revision_list):
        """Actually send properly formatted revisions to the database"""
        num_revisions = len(revision_list)
        log_id = str(uuid.uuid4())
        self.log.debug("Sending %d revisions" % num_revisions,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'revision',
                           'swh_num': num_revisions,
                           'swh_id': log_id,
                       })
        self.storage.revision_add(revision_list)
        self.log.debug("Done sending %d revisions" % num_revisions,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'revision',
                           'swh_num': num_revisions,
                           'swh_id': log_id,
                       })

    @retry(retry_on_exception=retry_loading, stop_max_attempt_number=3)
    def send_releases(self, release_list):
        """Actually send properly formatted releases to the database"""
        num_releases = len(release_list)
        log_id = str(uuid.uuid4())
        self.log.debug("Sending %d releases" % num_releases,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'release',
                           'swh_num': num_releases,
                           'swh_id': log_id,
                       })
        self.storage.release_add(release_list)
        self.log.debug("Done sending %d releases" % num_releases,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'release',
                           'swh_num': num_releases,
                           'swh_id': log_id,
                       })

    @retry(retry_on_exception=retry_loading, stop_max_attempt_number=3)
    def send_occurrences(self, occurrence_list):
        """Actually send properly formatted occurrences to the database"""
        num_occurrences = len(occurrence_list)
        log_id = str(uuid.uuid4())
        self.log.debug("Sending %d occurrences" % num_occurrences,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'occurrence',
                           'swh_num': num_occurrences,
                           'swh_id': log_id,
                       })
        self.storage.occurrence_add(occurrence_list)
        self.log.debug("Done sending %d occurrences" % num_occurrences,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'occurrence',
                           'swh_num': num_occurrences,
                           'swh_id': log_id,
                       })

    def dir_revision(self,
                     dir_path,
                     origin_url,
                     revision_date,
                     revision_offset,
                     revision_committer_date,
                     revision_committer_offset,
                     revision_type,
                     revision_message,
                     revision_author,
                     revision_committer):
        """Create a revision.

        """
        log_id = str(uuid.uuid4())

        self.log.debug('Creating origin for %s' % origin_url,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'origin',
                           'swh_num': 1,
                           'swh_id': log_id
                       })
        self.get_or_create_origin(origin_url)
        self.log.debug('Done creating origin for %s' % origin_url,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'origin',
                           'swh_num': 1,
                           'swh_id': log_id
                       })

    def bulk_send_blobs(self, objects, blobs, origin_id):
        """Format blobs as swh contents and send them to the database"""
        packet_size = self.config['content_packet_size']
        packet_size_bytes = self.config['content_packet_size_bytes']
        max_content_size = self.config['content_size_limit']

        send_in_packets(blobs, converters.blob_to_content,
                        self.send_contents, packet_size,
                        packet_size_bytes=packet_size_bytes,
                        log=self.log,
                        max_content_size=max_content_size,
                        origin_id=origin_id)

    def bulk_send_trees(self, objects, trees):
        """Format trees as swh directories and send them to the database"""
        packet_size = self.config['directory_packet_size']

        send_in_packets(trees, converters.tree_to_directory,
                        self.send_directories, packet_size,
                        objects=objects,
                        log=self.log)

    def bulk_send_commits(self, objects, commits):
        """Format commits as swh revisions and send them to the database"""
        packet_size = self.config['revision_packet_size']

        send_in_packets(commits, converters.commit_to_revision,
                        self.send_revisions, packet_size,
                        objects=objects,
                        log=self.log)

    def bulk_send_annotated_tags(self, objects, tags):
        """Format annotated tags (pygit2.Tag objects) as swh releases and send
        them to the database
        """
        packet_size = self.config['release_packet_size']

        send_in_packets(tags, converters.annotated_tag_to_release,
                        self.send_releases, packet_size,
                        log=self.log)

    def bulk_send_refs(self, objects, refs):
        """Format git references as swh occurrences and send them to the
        database
        """
        packet_size = self.config['occurrence_packet_size']
        send_in_packets(refs, lambda ref: ref,
                        self.send_occurrences, packet_size)

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

        def _revision_from(tree_hash, revision):
            full_rev = dict(revision)
            full_rev['directory'] = tree_hash
            full_rev['sha1_git'] = git.compute_revision_sha1_git(full_rev)
            return full_rev

        def _release_from(revision_hash, release):
            full_rel = dict(release)
            full_rel['revision'] = revision_hash
            full_rel['sha1_git'] = git.compute_release_sha1_git(full_rel)
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

        full_rev = _revision_from(tree_hash, revision)

        objects[GitType.COMM] = [full_rev]

        if release and 'name' in release:
            full_rel = _release_from(full_rev['sha1_git'], release)
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

    def load_dir(self, dir_path, objects, objects_per_path, refs, origin_id):
        if self.config['send_contents']:
            self.bulk_send_blobs(objects_per_path, objects[GitType.BLOB],
                                 origin_id)
        else:
            self.log.info('Not sending contents')

        if self.config['send_directories']:
            self.bulk_send_trees(objects_per_path, objects[GitType.TREE])
        else:
            self.log.info('Not sending directories')

        if self.config['send_revisions']:
            self.bulk_send_commits(objects_per_path, objects[GitType.COMM])
        else:
            self.log.info('Not sending revisions')

        if self.config['send_releases']:
            self.bulk_send_annotated_tags(objects_per_path,
                                          objects[GitType.RELE])
        else:
            self.log.info('Not sending releases')

        if self.config['send_occurrences']:
            self.bulk_send_refs(objects_per_path, refs)
        else:
            self.log.info('Not sending occurrences')

    def process(self, dir_path, origin, revision, release, occurrences):
        """Load a directory in backend.

        Args:
            - dir_path: source of the directory to import
            - origin: Dictionary origin
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
            - occurrences: List of occurrence dictionary.
              Information needed, keys are:
              - branch: occurrence's branch name
              - authority_id: authority id (e.g. 1 for swh)
              - validity: validity date (e.g. 2015-01-01 00:00:00+00)

        """
        def _occurrence_from(origin_id, revision_hash, occurrence):
            occ = dict(occurrence)
            occ.update({
                'revision': full_rev['sha1_git'],
                'origin': origin['id'],
            })
            return occ

        def _occurrences_from(origin_id, revision_hash, occurrences):
            full_occs = []
            for occurrence in occurrences:
                full_occ = _occurrence_from(origin_id,
                                            revision_hash,
                                            occurrence)
                full_occs.append(full_occ)
            return full_occs

        if not os.path.exists(dir_path):
            self.log.info('Skipping inexistant directory %s' % dir_path,
                          extra={
                              'swh_type': 'dir_repo_list_refs',
                              'swh_repo': dir_path,
                              'swh_num_refs': 0,
                          })
            return

        files = os.listdir(dir_path)
        if not files:
            self.log.info('Skipping empty directory %s' % dir_path,
                          extra={
                              'swh_type': 'dir_repo_list_refs',
                              'swh_repo': dir_path,
                              'swh_num_refs': 0,
                          })
            return

        if isinstance(dir_path, str):
            dir_path = dir_path.encode(sys.getfilesystemencoding())

        origin['id'] = self.storage.origin_add_one(origin)

        # to load the repository, walk all objects, compute their hash
        objects, objects_per_path = self.list_repo_objs(dir_path, revision,
                                                        release)

        full_rev = objects[GitType.COMM][0]  # only 1 revision

        full_occs = _occurrences_from(origin['id'],
                                      full_rev['sha1_git'],
                                      occurrences)

        self.load_dir(dir_path, objects, objects_per_path, full_occs,
                      origin['id'])
