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
Global configuration constants, variables and functions.
"""

import json
import sys
from os import listdir, mkdir
from os.path import dirname, join, expanduser, abspath
from shutil import copyfile
from dataclasses import dataclass
from .utils import download_file, get_file_name_from_url

USER_HOME = expanduser('~')
INSTALL_DIR = dirname(abspath(__file__))
HTTP_DIR = join(INSTALL_DIR, 'bundled', 'client')
PROJECTOR_SERVER_DIR = join(INSTALL_DIR, 'bundled', 'server')
PROJECTOR_MARKDOWN_PLUGIN_DIR = join(INSTALL_DIR, 'bundled', 'projector-markdown-plugin')
DEF_HTTP_PORT = 8889
DEF_PROJECTOR_PORT = 9999
COMPATIBLE_IDE_FILE = 'compatible_ide.json'


def get_server_file_name():
    """Returns full path to projector-server jar."""
    file_list = [file_name for file_name in listdir(PROJECTOR_SERVER_DIR)
                 if file_name.startswith('projector-server') and file_name.endswith('.jar')]

    if len(file_list) == 1:
        return join(PROJECTOR_SERVER_DIR, file_list[0])

    raise FileNotFoundError


try:
    SERVER_JAR = get_server_file_name()
except FileNotFoundError:
    print('Cannot find a Projector server. Please reinstall Projector.')
    sys.exit(2)

DEF_CONFIG_DIR = '.projector'

config_dir = join(USER_HOME, DEF_CONFIG_DIR)


def get_apps_dir():
    """Returns full path to applications directory."""
    return join(config_dir, 'apps')


def get_run_configs_dir():
    """Returns full path to run configs directory."""
    return join(config_dir, 'configs')


def get_download_cache_dir():
    """Returns full path to download cache directory."""
    return join(config_dir, 'cache')


def get_lib_dir():
    """Returns full path to lib directory."""
    return join(config_dir, 'lib')


def get_compatible_ide_file():
    """Returns full path to compatible ide file."""
    return join(get_lib_dir(), COMPATIBLE_IDE_FILE)


COMPATIBLE_IDE_FILE_URL = \
    'https://raw.githubusercontent.com/JetBrains/projector-installer/master/compatible_ide.json'


def download_compatible_ide_file():
    """Downloads compatible ide json file from github repository."""
    download_file(COMPATIBLE_IDE_FILE_URL, get_download_cache_dir())
    name = get_file_name_from_url(COMPATIBLE_IDE_FILE_URL)
    source = join(get_download_cache_dir(), name)
    destination = join(get_lib_dir(), name)
    copyfile(source, destination)


def copy_compatible_ide_file():
    """Copy compatible ide file from module to lib dir."""
    source = join(INSTALL_DIR, COMPATIBLE_IDE_FILE)
    destination = join(get_lib_dir(), COMPATIBLE_IDE_FILE)
    copyfile(source, destination)


@dataclass(frozen=True)
class CompatibleApp:
    """Compatible application entry."""
    name: str
    url: str


COMPATIBLE_APPS = []


def load_compatible_apps():
    """Loads compatible apps file to memory."""
    file_name = get_compatible_ide_file()

    with open(file_name, 'r') as file:
        data = json.load(file)

    for entry in data:
        app = CompatibleApp(entry['name'], entry['url'])
        COMPATIBLE_APPS.append(app)


def init_compatible_apps():
    """Initializes compatible apps list."""
    try:
        load_compatible_apps()
    except IOError:
        print('Cannot load compatible ide file, exiting...')
        sys.exit(2)


def init_config_dir():
    """Initializes global config directory."""
    mkdir(config_dir)
    mkdir(get_apps_dir())
    mkdir(get_run_configs_dir())
    mkdir(get_lib_dir())
    mkdir(get_download_cache_dir())
    # download_compatible_ide_file()
    copy_compatible_ide_file()
    init_compatible_apps()
