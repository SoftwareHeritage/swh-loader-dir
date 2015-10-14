from swh.loader.dir.tasks import LoadTarRepository

# Create a load tar instance (this will load a potential configuration file
# from ~/.config/swh/loader/tar.ini)
loadertar = LoadTarRepository()

tar_path = '/home/tony/Downloads/org2jekyll-0.1.8.tar'
info = {
    'dir_path': '/tmp/swh/loader/tar/org2jekyll',
}

loadertar.run(tar_path)
