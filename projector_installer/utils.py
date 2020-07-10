#  GNU General Public License version 2
#
#  Copyright (C) 2019-2020 JetBrains s.r.o.
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 2 only, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Misc utility functions.
"""

import tarfile
import zipfile
from os import listdir
from os.path import join, isfile, getsize, basename, isdir
from pathlib import Path
from shutil import copy

from click import progressbar, echo
import requests

CHUNK_SIZE = 4 * 1024 * 1024
PROGRESS_BAR_WIDTH = 50
PROGRESS_BAR_TEMPLATE = '[%(bar)s]  %(info)s'


def create_dir_if_not_exist(dir_name):
    """Creates given directory with all parents if it is not exist."""
    if not isdir(dir_name):
        path = Path(dir_name)
        path.mkdir(parents=True, exist_ok=True)


def copy_all_files(source, destination):
    """Copies all files from source directory to destination."""
    for file_name in listdir(source):
        from_path = join(source, file_name)
        to_path = join(destination, file_name)

        if isfile(from_path):
            copy(from_path, to_path)


def get_file_name_from_url(url):
    """
    Extracts file name from URL.
    """
    parts = url.split('/')
    result = parts[-1]
    pos = result.find('?')

    if pos != -1:
        result = result[:pos]

    return result


def download_file(url, destination):
    """
    Downloads file by given URL to destination dir.
    """
    file_name = get_file_name_from_url(url)
    file_path = join(destination, file_name)

    with requests.get(url, stream=True) as req:
        req.raise_for_status()
        total = int(req.headers['Content-Length'])

        if not isfile(file_path) or getsize(file_path) != total:
            echo(f'Downloading {file_name}')
            with open(file_path, 'wb') as file, \
                    progressbar(length=total,
                                width=PROGRESS_BAR_WIDTH,
                                bar_template=PROGRESS_BAR_TEMPLATE) as progress_bar:
                for chunk in req.iter_content(CHUNK_SIZE):
                    if chunk:
                        file.write(chunk)
                        progress_bar.update(len(chunk))

    return file_path


def unpack_tar_file(file_path, destination):
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


def unpack_zip_file(file_path, destination):
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
