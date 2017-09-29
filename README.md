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

send_contents: True
send_directories: True
send_revisions: True
send_releases: True
send_occurrences: True
# nb of max contents to send for storage
content_packet_size: 100
# 100 Mib of content data
content_packet_block_size_bytes: 104857600
# limit for swh content storage for one blob (beyond that limit, the
# content's data is not sent for storage)
content_packet_size_bytes: 1073741824
directory_packet_size: 250
revision_packet_size: 100
release_packet_size: 100
occurrence_packet_size: 100
```

## Run

To run the loader, you can use either:

- python3's toplevel
- celery

### Toplevel

Load directory directly from code or toplevel:

``` Python
from swh.loader.dir.loader import DirLoader

dir_path = '/path/to/directory

# Fill in those
origin = {'url': 'some-origin', 'type': 'dir'}
visit_date = 'Tue, 3 May 2017 17:16:32 +0200'
release = None
revision = {}
occurrence = {}

DirLoader().load(dir_path, origin, visit_date, revision, release, [occurrence])
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
