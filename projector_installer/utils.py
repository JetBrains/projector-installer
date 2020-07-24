# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""
Misc utility functions.
"""

import tarfile
import zipfile
from os import listdir
from os.path import join, isfile, getsize, basename, isdir
from pathlib import Path
from shutil import copy
from urllib.request import urlopen
from typing import Optional

from click import progressbar, echo

CHUNK_SIZE = 4 * 1024 * 1024
PROGRESS_BAR_WIDTH = 50
PROGRESS_BAR_TEMPLATE = '[%(bar)s]  %(info)s'


def create_dir_if_not_exist(dir_name: str) -> None:
    """Creates given directory with all parents if it is not exist."""
    if not isdir(dir_name):
        path = Path(dir_name)
        path.mkdir(parents=True, exist_ok=True)


def copy_all_files(source: str, destination: str) -> None:
    """Copies all files from source directory to destination."""
    for file_name in listdir(source):
        from_path = join(source, file_name)
        to_path = join(destination, file_name)

        if isfile(from_path):
            copy(from_path, to_path)


def get_file_name_from_url(url: str) -> str:
    """
    Extracts file name from URL.
    """
    parts = url.split('/')
    result = parts[-1]
    pos = result.find('?')

    if pos != -1:
        result = result[:pos]

    return result


def download_file(url: str, destination: str, timeout: Optional[int] = None,
                  silent: Optional[bool] = False) -> str:
    """
    Downloads file by given URL to destination dir.
    """
    file_name = get_file_name_from_url(url)
    file_path = join(destination, file_name)

    with urlopen(url, timeout=timeout) as resp:
        code: int = resp.getcode()

        if code != 200:
            raise IOError(f'Bad HTTP response code: {code}')

        total = int(resp.getheader('Content-Length'))

        if not isfile(file_path) or getsize(file_path) != total:

            if not silent:
                echo(f'Downloading {file_name}')

            with open(file_path, 'wb') as file, \
                    progressbar(length=total,
                                width=PROGRESS_BAR_WIDTH,
                                bar_template=PROGRESS_BAR_TEMPLATE) as progress_bar:

                while True:
                    chunk = resp.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    file.write(chunk)

                    if not silent:
                        progress_bar.update(len(chunk))

    return file_path


def unpack_tar_file(file_path: str, destination: str) -> str:
    """ Unpacks given file in destination directory. """
    print(f'Unpacking {basename(file_path)}')

    with tarfile.open(file_path) as tar_file:
        members = tar_file.getmembers()
        dir_name = members[0].name.split('/')[0]

        with progressbar(length=len(members), width=PROGRESS_BAR_WIDTH,
                         bar_template=PROGRESS_BAR_TEMPLATE) as progress_bar:
            for member in members:
                tar_file.extract(member, destination)
                progress_bar.update(1)

    return dir_name


def unpack_zip_file(file_path: str, destination: str) -> str:
    """ Unpacks given file in destination directory. """
    print(f'Unpacking {basename(file_path)}')

    with zipfile.ZipFile(file_path) as zip_file:
        file_names = zip_file.namelist()
        dir_name = file_names[0].split('/')[0]

        with progressbar(length=len(file_names), width=PROGRESS_BAR_WIDTH,
                         bar_template=PROGRESS_BAR_TEMPLATE) as progress_bar:
            for file_name in file_names:
                zip_info = zip_file.getinfo(file_name)
                zip_file.extract(zip_info, destination)
                progress_bar.update(1)

    return dir_name
