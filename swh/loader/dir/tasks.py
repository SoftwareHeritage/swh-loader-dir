# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.loader.dir.loader import DirLoader
from swh.loader.core import tasks


class LoadDirRepository(tasks.LoaderCoreTask):
    """Import a directory to Software Heritage

    """
    task_queue = 'swh_loader_dir'

    def run(self, dir_path, origin, revision, release, occurrences):
        """Import a directory.

        Args:
            cf. swh.loader.dir.loader.run docstring

        """
        storage = DirLoader().storage

        origin['id'] = storage.origin_add_one(origin)

        fetch_history_id = self.open_fetch_history(storage, origin['id'])

        result = DirLoader(origin['id']).process(dir_path,
                                                 origin,
                                                 revision,
                                                 release,
                                                 occurrences)

        self.close_fetch_history(storage, fetch_history_id, result)
