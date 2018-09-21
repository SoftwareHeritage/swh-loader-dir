SWH-loader-dir
===================

The Software Heritage Directory Loader is a tool and a library.

Its sole purpose is to walk a local directory and inject into the SWH
dataset all unknown contained files from that directory structure.


## Configuration

The loader needs a configuration file in *`{/etc/softwareheritage |
~/.config/swh | ~/.swh}`/loader/dir.yml*.

This file should be similar to this (adapt according to your needs):

``` yaml
storage:
  cls: remote
  args:
    url: http://localhost:5002/
```

## Run

To run the loader, you can use either:

- python3's toplevel
- celery

### Toplevel

Load directory directly from code or toplevel:

``` Python
dir_path = '/home/storage/dir/'

# Fill in those
origin = {'url': 'some-origin', 'type': 'dir'}
visit_date = 'Tue, 3 May 2017 17:16:32 +0200'
revision = {
    'author': {'name': 'some', 'fullname': 'one', 'email': 'something'},
    'committer': {'name': 'some', 'fullname': 'one', 'email': 'something'},
    'message': '1.0 Released',
    'date': None,
    'committer_date': None,
    'type': 'tar',
    'metadata': {}
}
import logging
logging.basicConfig(level=logging.DEBUG)

from swh.loader.dir.tasks import LoadDirRepository
l = LoadDirRepository()
l.run_task(dir_path=dir_path, origin=origin, visit_date=visit_date,
           revision=revision, release=None, branch_name='master')
```

### Celery

To use celery, add the following entries in the
*`{/etc/softwareheritage | ~/.config/swh | ~/.swh}`/worker.yml*` file:

``` yaml
task_modules:
  - swh.loader.dir.tasks
task_queues:
  - swh_loader_dir
```

cf. [swh-core's documentation](https://forge.softwareheritage.org/diffusion/DCORE/browse/master/README.md) for
more details.

You can then send the following message to the task queue:

``` Python
from swh.loader.dir.tasks import LoadDirRepository

# Fill in those
origin = {'url': 'some-origin', 'type': 'dir'}
visit_date = 'Tue, 3 May 2017 17:16:32 +0200'
release = None
revision = {}
occurrence = {}

# Send message to the task queue
LoaderDirRepository().run(('/path/to/dir', origin, visit_date, revision, release, [occurrence]))
```
