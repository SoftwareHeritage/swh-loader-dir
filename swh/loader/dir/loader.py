# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import uuid
import traceback
import os
import psycopg2

from retrying import retry
from enum import Enum

from swh.core import config

from . import converters
from .utils import get_objects_per_object_type


class DirType(Enum):
    DIR='directory'
    CON='content'
    REV='revision'
    REL='release'

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

    def get_or_create_origin(self, origin_url):
        origin = converters.origin_url_to_origin(origin_url)

        origin['id'] = self.storage.origin_add_one(origin)

        return origin

    def dir_origin(self, root_dir, origin_url):
        log_id = str(uuid.uuid4())
        self.log.debug('Creating origin for %s' % origin_url,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'origin',
                           'swh_num': 1,
                           'swh_id': log_id
                       })
        origin = self.get_or_create_origin(origin_url)
        self.log.debug('Done creating origin for %s' % origin_url,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'origin',
                           'swh_num': 1,
                           'swh_id': log_id
                       })

        return origin

    def dir_revision(self,
                     root_dir,
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
        self.log.debug('Creating origin for %s' % origin_url,
                       extra={
                           'swh_type': 'storage_send_start',
                           'swh_content_type': 'origin',
                           'swh_num': 1,
                           'swh_id': log_id
                       })
        origin = self.get_or_create_origin(origin_url)
        self.log.debug('Done creating origin for %s' % origin_url,
                       extra={
                           'swh_type': 'storage_send_end',
                           'swh_content_type': 'origin',
                           'swh_num': 1,
                           'swh_id': log_id
                       })



    def bulk_send_blobs(self, root_dir, blobs, origin_id):
        """Format blobs as swh contents and send them to the database"""
        packet_size = self.config['content_packet_size']
        packet_size_bytes = self.config['content_packet_size_bytes']
        max_content_size = self.config['content_size_limit']

        send_in_packets(blobs, converters.blob_to_content,
                        self.send_contents, packet_size, root_dir=root_dir,
                        packet_size_bytes=packet_size_bytes,
                        log=self.log, max_content_size=max_content_size,
                        origin_id=origin_id)

    def bulk_send_trees(self, root_dir, trees):
        """Format trees as swh directories and send them to the database"""
        packet_size = self.config['directory_packet_size']

        send_in_packets(trees, converters.tree_to_directory,
                        self.send_directories, packet_size, root_dir=root_dir,
                        log=self.log)

    def bulk_send_commits(self, root_dir, commits):
        """Format commits as swh revisions and send them to the database"""
        packet_size = self.config['revision_packet_size']

        send_in_packets(commits, converters.commit_to_revision,
                        self.send_revisions, packet_size, root_dir=root_dir,
                        log=self.log)

    def bulk_send_annotated_tags(self, root_dir, tags):
        """Format annotated tags (pygit2.Tag objects) as swh releases and send
        them to the database
        """
        packet_size = self.config['release_packet_size']

        send_in_packets(tags, converters.annotated_tag_to_release,
                        self.send_releases, packet_size, root_dir=root_dir,
                        log=self.log)

    def bulk_send_refs(self, root_dir, refs):
        """Format git references as swh occurrences and send them to the
        database
        """
        packet_size = self.config['occurrence_packet_size']

        send_in_packets(refs, converters.ref_to_occurrence,
                        self.send_occurrences, packet_size)

    def compute_dir_ref(self, root_dir,
                       branch,
                       revision_hash,
                       origin_id,
                       authority_id,
                       validity):
        """List all the refs from the given root directory root_dir.

        Args:
            - root_dir: the root directory
            - branch: occurrence's branch name
            - revision_hash: the revision hash
            - origin_id (int): the id of the origin from which the root_dir is
                taken
            - validity (datetime.datetime): the validity date for the
                repository's refs
            - authority_id (int): the id of the authority on `validity`.

        Returns:
            One dictionary with keys:
                - branch (str): name of the ref
                - revision (sha1_git): revision pointed at by the ref
                - origin (int)
                - validity (datetime.DateTime)
                - authority (int)
            Compatible with occurrence_add.
        """

        log_id = str(uuid.uuid4())

        self.log.debug("Computing occurrence %s representation at %s" % (
            branch, revision_hash), extra={
                'swh_type': 'computing_occurrence_dir',
                'swh_name': branch,
                'swh_target': str(revision_hash),
                'swh_id': log_id,
            })

        return {
            'branch': branch,
            'revision': revision_hash,
            'origin': origin_id,
            'validity': validity,
            'authority': authority_id,
        }

    def list_repo_objs(self, root_dir):
        """List all objects from root_dir.

        Args:
            - root_dir (path): the directory to list

        Returns:
            a dict containing lists of `Oid`s with keys for each object type:
            - CONTENT
            - DIRECTORY
        """
        # log_id = str(uuid.uuid4())

        # self.log.info("Started listing %s" % root_dir.path, extra={
        #     'swh_type': 'git_list_objs_start',
        #     'swh_repo': root_dir.path,
        #     'swh_id': log_id,
        # })
        # objects = get_objects_per_object_type(root_dir)
        # self.log.info("Done listing the objects in %s: %d contents, "
        #               "%d directories, %d revisions, %d releases" % (
        #                  root_dir.path,
        #                  len(objects[GIT_OBJ_BLOB]),
        #                  len(objects[GIT_OBJ_TREE]),
        #                  len(objects[GIT_OBJ_COMMIT]),
        #                  len(objects[GIT_OBJ_TAG]),
        #               ), extra={
        #                   'swh_type': 'git_list_objs_end',
        #                   'swh_repo': root_dir.path,
        #                   'swh_num_blobs': len(objects[GIT_OBJ_BLOB]),
        #                   'swh_num_trees': len(objects[GIT_OBJ_TREE]),
        #                   'swh_num_commits': len(objects[GIT_OBJ_COMMIT]),
        #                   'swh_num_tags': len(objects[GIT_OBJ_TAG]),
        #                   'swh_id': log_id,
        #               })
        # return objects

        return []

    def open_dir(self, root_dir):
        return root_dir

    def load_dir(self, root_dir, objects, refs, origin_id):
        if self.config['send_contents']:
            self.bulk_send_blobs(root_dir, objects[DirType.CON], origin_id)
        else:
            self.log.info('Not sending contents')

        if self.config['send_directories']:
            self.bulk_send_trees(root_dir, objects[DirType.DIR])
        else:
            self.log.info('Not sending directories')

        if self.config['send_revisions']:
            self.bulk_send_commits(root_dir, objects[DirType.REV])
        else:
            self.log.info('Not sending revisions')

        if self.config['send_releases']:
            self.bulk_send_annotated_tags(root_dir, objects[DirType.REL])
        else:
            self.log.info('Not sending releases')

        if self.config['send_occurrences']:
            self.bulk_send_refs(root_dir, refs)
        else:
            self.log.info('Not sending occurrences')

    def compute_revision_hash_from(self,
                                   root_dir,
                                   revision_date,
                                   revision_offset,
                                   revision_committer_date,
                                   revision_committer_offset,
                                   revision_type,
                                   revision_message,
                                   revision_author,
                                   revision_committer):
        """Compute the revision git sha1 from the root_dir.

        """
        # FIXME: actually do it
        return {'git_sha1': ''}

    def process(self, root_dir, extra_config):
        # Checks the input
        try:
            files = os.listdir(root_dir)
            if files == []:
                self.log.info('Skipping empty directory %s' % root_dir, extra={
                    'swh_type': 'dir_repo_list_refs',
                    'swh_repo': root_dir,
                    'swh_num_refs': 0,
                })
                return
        except FileNotFoundError:
            self.log.info('Skipping inexistant directory %s' % root_dir, extra={
                'swh_type': 'dir_repo_list_refs',
                'swh_repo': root_dir,
                'swh_num_refs': 0,
            })
            return

        # Open repository
        root_dir = self.open_dir(root_dir)

        # Add origin to storage if needed, use the one from config if not
        origin = self.dir_origin(root_dir, self.config['origin_url'])

        # Compute revision information (mixed from outside input + dir content)
        revision = self.compute_revision_hash_from(
            root_dir,
            self.config['revision_date'],
            self.config['revision_offset'],
            self.config['revision_committer_date'],
            self.config['revision_committer_offset'],
            self.config['revision_type'],
            self.config['revision_message'],
            self.config['revision_author'],
            self.config['revision_committer'])

        # Parse all the refs from our root_dir
        ref = self.compute_dir_ref(root_dir,
                                   origin['id'],
                                   self.config['branch'],
                                   revision['git_sha1'],
                                   self.config['authority_id'],
                                   self.config['validity'])

        # We want to load the repository, walk all the objects
        objects = self.list_repo_objs(root_dir)

        # Finally, load the repository
        self.load_dir(root_dir, objects, [ref], origin['id'])