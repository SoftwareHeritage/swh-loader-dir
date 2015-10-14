from swh.loader.dir.tasks import LoadTarRepository

# Create a load tar instance (this will load a potential configuration file
# from ~/.config/swh/loader/tar.ini)
loadertar = LoadTarRepository()

tar_path = '/home/tony/work/inria/repo/linux.tgz'
loadertar.delay(tar_path)
