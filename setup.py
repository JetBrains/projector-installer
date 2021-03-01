# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""projector-installer setup file."""

from shutil import copyfile, rmtree
from os.path import isfile, join
from os import remove
from typing import List
from setuptools import setup  # type: ignore
from setuptools.command.install import install  # type: ignore
from setuptools import Command

from projector_installer.utils import create_dir_if_not_exist, download_file, unpack_zip_file, \
    get_file_name_from_url, copy_all_files

from projector_installer.global_config import BUNDLED_DIR, SERVER_DIR


def copy_license() -> None:
    """Copy license file to package"""
    if isfile('license/LICENSE.txt'):
        copyfile('license/LICENSE.txt', 'projector_installer/LICENSE.txt')


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

PACKAGE_DIR = 'projector_installer'
bundled_dir = join(PACKAGE_DIR, BUNDLED_DIR)
server_dir = join(bundled_dir, SERVER_DIR)

PROJECTOR_SERVER_URL: str = 'https://github.com/JetBrains/projector-server/releases/' \
                            'download/v1.0.0/projector-server-v1.0.0.zip'


def download_server(to_dir: str) -> None:
    """Download and  unpack projector server"""
    download_file(PROJECTOR_SERVER_URL, to_dir)
    file_path = join(to_dir, get_file_name_from_url(PROJECTOR_SERVER_URL))
    dir_name = unpack_zip_file(file_path, to_dir)
    temp_dir = join(to_dir, dir_name)
    jars_path = join(temp_dir, 'lib')
    copy_all_files(jars_path, to_dir)
    rmtree(temp_dir)
    remove(file_path)


def download_bundled_data() -> None:
    """Downloads data to bundle in package"""

    rmtree(bundled_dir, ignore_errors=True)
    create_dir_if_not_exist(bundled_dir)
    create_dir_if_not_exist(server_dir)
    download_server(server_dir)


class BundleCommand(Command):
    """Download bundled data."""
    description = 'Download bundled data.'
    user_options: List[str] = []

    def initialize_options(self) -> None:
        """Abstract method stub"""

    def finalize_options(self) -> None:
        """Abstract method stub"""

    def run(self) -> None:
        """Run command."""
        copy_license()
        download_bundled_data()


class CustomInstallCommand(install):
    """
    Customized install command.
    """

    def run(self) -> None:
        """
        Copies add data to package.
        """
        copy_license()
        download_bundled_data()
        install.run(self)


setup(
    install_requires=requirements,
    setup_requires=['click'],
    cmdclass={
        'bundle': BundleCommand,
        'install': CustomInstallCommand
    }
)
