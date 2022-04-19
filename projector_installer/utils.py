# Copyright 2000-2022 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""
Misc utility functions.
"""
import os
import platform
import stat
import sys
import io
import json
import tarfile
import zipfile
import subprocess
import secrets
import string
from os import listdir, remove, makedirs, chmod

from os.path import join, isfile, getsize, basename, isdir, realpath, expandvars, expanduser
from shutil import copy
from urllib.parse import ParseResult, urlparse
from urllib.request import urlopen
from typing import Optional, BinaryIO, cast, List, Any

import netifaces  # type: ignore
from click import progressbar, echo

CHUNK_SIZE = 4 * 1024 * 1024
PROGRESS_BAR_WIDTH = 50
PROGRESS_BAR_TEMPLATE = '[%(bar)s]  %(info)s'
DEF_TOKEN_LEN = 20
DOCKER_VENDOR = '02:42'


def create_dir_if_not_exist(dir_name: str) -> None:
    """Creates given directory with all parents if it is not exist."""
    if not isdir(dir_name):
        makedirs(dir_name, mode=0o700, exist_ok=True)


def remove_file_if_exist(file_name: str) -> None:
    """Removes existing file"""
    if isfile(file_name):
        remove(file_name)


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
    parsed_url: ParseResult = urlparse(url)

    with urlopen(url, timeout=timeout) as resp:
        code: int = resp.getcode()

        if parsed_url.scheme != 'file' and code != 200:
            raise IOError(f'Bad HTTP response code: {code}')

        total = int(resp.getheader('Content-Length')) if parsed_url.scheme != 'file' \
            else os.path.getsize(parsed_url.path)

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


def ensure_writable(path: str) -> None:
    """Makes file writable by owner"""
    if isfile(path):
        file_stats = os.stat(path)

        if (file_stats.st_mode & stat.S_IWUSR) == 0:
            chmod(path, file_stats.st_mode | stat.S_IWUSR)


def unpack_tar_file(file_path: str, destination: str) -> str:
    """ Unpacks given file in destination directory. """
    print(f'Unpacking {basename(file_path)}')

    with tarfile.open(file_path) as tar_file:
        members = tar_file.getmembers()
        dir_name = members[0].name.split('/')[0]

        with progressbar(length=len(members), width=PROGRESS_BAR_WIDTH,
                         bar_template=PROGRESS_BAR_TEMPLATE) as progress_bar:
            for member in members:
                out_member_path = join(destination, member.name)
                tar_file.extract(member=member, path=destination)
                ensure_writable(out_member_path)  # workaround for MPS licenses
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


def get_java_version(java_path: str) -> str:
    """Returns java version for given java binary path"""
    proc = subprocess.Popen([java_path, '-version'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    line = io.TextIOWrapper(cast(BinaryIO, proc.stderr), encoding='utf-8').readline()
    proc.wait()
    values = line.split(' ')
    version = values[2]
    return version.strip('"')


def is_inside_docker() -> bool:
    """Detects if we run inside docker container"""
    return isfile('/.dockerenv')


def is_docker_interface(ifs: Any) -> bool:
    """Returns True if given interface belongs to docker"""
    addresses = netifaces.ifaddresses(ifs)

    if netifaces.AF_LINK in addresses:
        for mac in addresses[netifaces.AF_LINK]:
            if mac['addr'][:5] == DOCKER_VENDOR:
                return True

    return False


def get_local_addresses() -> List[str]:
    """Returns list of local ip addresses."""
    interfaces = netifaces.interfaces()
    res = []

    for ifs in interfaces:

        if not is_inside_docker() and is_docker_interface(ifs):
            continue

        addresses = netifaces.ifaddresses(ifs)

        if netifaces.AF_INET in addresses:
            ipv4 = addresses[netifaces.AF_INET]

            for ips in ipv4:
                res.append(ips['addr'])

    return res


def get_json(url: str, timeout: float) -> Any:
    """Returns dictionary - parsed json, retrieved via given URL"""
    resp = urlopen(url, timeout=timeout)
    code = resp.getcode()

    if code != 200:
        raise IOError(f'HTTP error code: {code}')

    return json.loads(resp.read().decode())


def generate_token(length: int = DEF_TOKEN_LEN) -> str:
    """Generates token to access server's secrets"""
    return generate_random_password(length=length)


DEF_PASSWORD_LEN = 20


def generate_random_password(length: int = DEF_PASSWORD_LEN) -> str:
    """Generate random alphanumeric password with given length"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_distributive_name() -> str:
    """Try to obtain distributive name from /etc/lsb-release"""
    try:
        with open('/etc/lsb-release', mode='r', encoding='utf-8') as file:
            for line in file:
                if line.startswith('DISTRIB_ID'):
                    parts = line.split('=')

                    if len(parts) > 1:
                        return parts[1].strip()

    except OSError:
        pass

    return ''


def expand_path(path: str) -> str:
    """Performs full path expansion"""
    return realpath(expandvars(expanduser(path)))


def is_in_venv() -> bool:
    """Check if process run in Python virtual environment"""

    def get_base_prefix() -> Optional[str]:
        """Safe get the sys.base_prefix property"""
        return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix

    return get_base_prefix() != sys.prefix


def is_linux_x86_64() -> bool:
    """Returns true for Linux x86_64 machine"""
    return platform.system() == 'Linux' and platform.machine() == 'x86_64'
