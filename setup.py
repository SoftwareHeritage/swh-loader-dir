from setuptools import setup


def parse_requirements():
    requirements = []
    with open('requirements.txt') as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)

    return requirements


setup(
    name='swh.loader.dir',
    description='Software Heritage Directory Loader',
    author='Software Heritage developers',
    author_email='swh-devel@inria.fr',
    url='https://forge.softwareheritage.org/diffusion/DLDDIR',
    packages=['swh.loader.dir', 'swh.loader.dir.tests'],
    scripts=['bin/swh-loader-dir'],
    install_requires=parse_requirements(),
    setup_requires=['vcversioner'],
    vcversioner={},
    include_package_data=True,
)
