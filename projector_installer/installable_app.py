#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""InstallableApp class and related stuff"""
import json
import socket
from os import remove
from os.path import join
from tempfile import gettempdir
from typing import List, Tuple, Any
from enum import Enum, auto
from urllib.error import URLError

from .utils import download_file, get_file_name_from_url

COMPATIBLE_IDE_FILE_URL: str = \
    'https://raw.githubusercontent.com/JetBrains/projector-installer/master/' \
    'projector_installer/compatible_ide.json'


class IDEKind(Enum):
    """Known IDE kinds"""
    Unknown = auto()
    Idea_Community = auto()
    Idea_Ultimate = auto()
    PyCharm_Community = auto()
    PyCharm_Professional = auto()
    CLion = auto()
    GoLand = auto()
    DataGrip = auto()
    PhpStorm = auto()
    WebStorm = auto()
    RubyMine = auto()


class InstallableApp:
    """Installable application entry."""

    def __init__(self, name: str, url: str, kind: IDEKind) -> None:
        self.name: str = name
        self.url: str = url
        self.kind = kind

    def __key__(self) -> Tuple[str, str]:
        return self.name, self.url

    def __eq__(self, other: object) -> bool:
        if isinstance(other, InstallableApp):
            return self.__key__() == other.__key__()

        return False

    def __hash__(self) -> int:
        return hash(self.__key__())


def _parse_entry(entry: Any) -> InstallableApp:
    """Get InstallableApp from JSON array entry"""

    try:
        kind = IDEKind[entry['kind']]
    except KeyError:
        kind = IDEKind.Unknown

    return InstallableApp(entry['name'], entry['url'], kind)


def load_installable_apps_from_file(file_name: str) -> List[InstallableApp]:
    """Loads installable app list from json file."""
    with open(file_name, 'r') as file:
        data = json.load(file)

    return [_parse_entry(entry) for entry in data]


def download_compatible_apps() -> str:
    """Downloads compatible ide json file from github repository."""

    try:
        download_file(COMPATIBLE_IDE_FILE_URL, gettempdir(), timeout=3, silent=True)
        name = get_file_name_from_url(COMPATIBLE_IDE_FILE_URL)
        file_name = join(gettempdir(), name)

        return file_name
    except (URLError, socket.timeout):
        return ''


def load_compatible_apps_from_github() -> List[InstallableApp]:
    """Loads compatible app list from github repo"""
    file_name = download_compatible_apps()
    res = load_installable_apps_from_file(file_name) if file_name else []
    remove(file_name)
    return res


def load_compatible_apps(file_name: str) -> List[InstallableApp]:
    """Loads from file and from github and merges results"""
    local_list = load_installable_apps_from_file(file_name)
    github_list = load_compatible_apps_from_github()

    return list(set(local_list) | set(github_list))

# # https://data.services.jetbrains.com/products?code=IIU%2CIIC&release.type=release
# PRODUCTS_URL = 'https://data.services.jetbrains.com/products'
