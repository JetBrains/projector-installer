#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Product class and related stuff"""
import json
import socket
import sys
from os import remove
from os.path import join, dirname, abspath
from tempfile import gettempdir
from typing import List, Tuple, Any, Optional
from enum import Enum, auto
from urllib.error import URLError
from distutils.version import LooseVersion
from dataclasses import dataclass

from .global_config import LONG_NETWORK_TIMEOUT
from .utils import download_file, get_file_name_from_url, get_json

COMPATIBLE_IDE_FILE: str = join(dirname(abspath(__file__)), 'compatible_ide.json')

COMPATIBLE_IDE_FILE_URL: str = \
    'https://raw.githubusercontent.com/JetBrains/projector-installer/master/' \
    'projector_installer/compatible_ide.json'


# pylint: disable=C0103
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


@dataclass
class Product:
    """Installable application entry."""

    name: str
    url: str
    kind: IDEKind
    ver: LooseVersion = LooseVersion('0.0.0')

    def __key__(self) -> Tuple[str, str]:
        return self.name, self.url

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Product):
            return self.__key__() == other.__key__()

        return False

    def __hash__(self) -> int:
        return hash(self.__key__())

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f'Product({self.name}, {self.url}, {self.kind})'


COMPATIBLE_APPS: List[Product] = []


def _parse_entry(entry: Any) -> Product:
    """Get Product from JSON array entry"""

    try:
        kind = IDEKind[entry['kind']]
    except KeyError:
        kind = IDEKind.Unknown

    ver = LooseVersion(entry['name'].split(' ')[-1])

    return Product(entry['name'], entry['url'], kind, ver)


def load_installable_apps_from_file(file_name: str) -> List[Product]:
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


def load_compatible_apps_from_github() -> List[Product]:
    """Loads compatible app list from github repo"""
    file_name = download_compatible_apps()
    res = load_installable_apps_from_file(file_name) if file_name else []
    remove(file_name)
    return res


def load_compatible_apps(file_name: str) -> List[Product]:
    """Loads from file and from github and merges results"""
    local_list = load_installable_apps_from_file(file_name)
    github_list = load_compatible_apps_from_github()

    return list(set(local_list) | set(github_list))


def init_compatible_apps() -> List[Product]:
    """Initializes compatible apps list."""
    try:
        return load_compatible_apps(COMPATIBLE_IDE_FILE)
    except IOError as error:
        print(f'Cannot load compatible ide file: {str(error)}. Exiting...')
        sys.exit(2)


PRODUCTS_URL = 'https://data.services.jetbrains.com/products'

KIND2CODE = {
    IDEKind.Idea_Community: 'IIC',
    IDEKind.Idea_Ultimate: 'IIU',
    IDEKind.PyCharm_Community: 'PCC',
    IDEKind.PyCharm_Professional: 'PCP',
    IDEKind.CLion: 'CL',
    IDEKind.GoLand: 'GO',
    IDEKind.DataGrip: 'DG',
    IDEKind.PhpStorm: 'PS',
    IDEKind.WebStorm: 'WS',
    IDEKind.RubyMine: 'RM',
}

# All releases before this version considered as unsupported
EARLIEST_COMPATIBLE_VERSION = LooseVersion('2019.3')


def get_product_releases(kind: IDEKind, timeout: float) -> List[Product]:
    """Retrieves list of product releases from JB products service"""
    url = f'{PRODUCTS_URL}?code={KIND2CODE[kind]}&release.type=release'
    data = get_json(url, timeout=timeout)
    res = []

    for entry in data:
        name = entry['name']
        releases = entry['releases']

        for release in releases:
            ver = release['version']

            if LooseVersion(ver) < EARLIEST_COMPATIBLE_VERSION:
                continue

            downloads = release['downloads']

            if 'linux' not in downloads:
                continue

            link = downloads['linux']['link']
            res.append(Product(f'{name} {ver}', link, kind, ver))

    return res


def get_compatible_products(kind: IDEKind) -> List[Product]:
    """Returns list of all compatible apps with given kind"""
    apps = init_compatible_apps()
    return [app for app in apps if app.kind == kind]


def filter_app_by_name_pattern(data: List[Product], pattern: Optional[str] = None) -> List[Product]:
    """Filters given Product list by given name pattern.
    Returns list with single element on exact match."""

    apps = [app for app in data
            if pattern is None or app.name.lower().find(pattern.lower()) != -1]

    if pattern:
        for app in apps:
            if pattern.lower() == app.name.lower():
                return [app]

    return apps


def get_compatible_apps(kind: IDEKind, pattern: Optional[str] = None) -> List[Product]:
    """Returns list of compatible apps, matched given kind and pattern."""
    apps = get_compatible_products(kind)
    return filter_app_by_name_pattern(apps, pattern)


def get_all_apps(kind: IDEKind, pattern: Optional[str] = None) -> List[Product]:
    """Returns list of all released apps, matched given kind and pattern."""
    apps = get_product_releases(kind, timeout=LONG_NETWORK_TIMEOUT)
    return filter_app_by_name_pattern(apps, pattern)
