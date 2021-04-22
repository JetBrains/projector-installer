#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Check updates module"""
from distutils.version import LooseVersion
import socket
from os import environ
from typing import Optional, Any
from urllib.error import URLError
import click

from .global_config import get_changelog_url, LONG_NETWORK_TIMEOUT, \
    SHORT_NETWORK_TIMEOUT, INSTALL_DIR, USER_HOME

from .timeout import timeout, TimeoutException
from .utils import get_json, is_in_venv

from .version import __version__

PYPI_PRODUCT_URL = 'https://pypi.org/pypi/projector-installer/json'


def print_self_update_warning() -> None:
    """Print PIP incompatibility warning"""
    click.secho('PIP version is incompatible with self-upgrade feature.\n'
                'Try to upgrade pip to more recent version using command:\n\t'
                'python3 -m pip install -U pip\n', bold=True, fg='yellow')


try:
    # pylint: disable=import-outside-toplevel
    from pip._internal.cli.main import main as pip_main  # type: ignore
except ModuleNotFoundError:
    print_self_update_warning()


def get_latest_installer_version(time: float) -> Optional[Any]:
    """Retrieve projector-installer version from pypi with given timeout"""
    try:
        res = get_json(PYPI_PRODUCT_URL, timeout=time)
        return res['info']['version']
    except (URLError, socket.timeout):
        return None


def is_newer_than_current(ver_to_check: str) -> bool:
    """
    Compares given version with current.
    Returns True if given version is more recent
    """
    current_version = LooseVersion(__version__)
    pypi_version = LooseVersion(ver_to_check)
    return current_version < pypi_version


def is_update_available() -> bool:
    """Returns true if new projector-installer version
    is available on pypi
    """
    pypi_ver = get_latest_installer_version(LONG_NETWORK_TIMEOUT)

    if pypi_ver is None:
        return False

    return is_newer_than_current(pypi_ver)


UPDATE_COMMAND = 'projector self-update'


@timeout(SHORT_NETWORK_TIMEOUT)
def get_latest_version_fast() -> Optional[Any]:
    """Decorated for fast check"""
    return get_latest_installer_version(LONG_NETWORK_TIMEOUT)


def check_for_projector_updates() -> None:
    """Check if new projector version is available"""

    try:
        pypi_version = get_latest_version_fast()
    except TimeoutException:
        click.echo('Checking for updates ... ', nl=False)
        pypi_version = get_latest_installer_version(LONG_NETWORK_TIMEOUT)
        click.echo('done.')

    if pypi_version is None:
        return

    if is_newer_than_current(pypi_version):
        msg = f'\nNew version {pypi_version} of projector-installer is available ' \
              f'(ver. {__version__} is installed)!\n' \
              f'Changelog: {get_changelog_url(pypi_version)}\n' \
              f'To update use command: {UPDATE_COMMAND}\n'
        click.secho(msg, bold=True)


def is_user_install() -> bool:
    """Returns True if projector _probably_ installed with --user option"""
    return INSTALL_DIR.startswith(USER_HOME) and not is_in_venv()


def self_update(version: str) -> None:
    """Update projector-installer"""
    args = ['install', f'projector-installer=={version}', '--upgrade']
    proxy = environ.get('http_proxy')

    if proxy:
        args.append('--proxy')
        args.append(proxy)

    if is_user_install():
        args.append('--user')

    try:
        pip_main(args)
    except NameError:
        print_self_update_warning()
