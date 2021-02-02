# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Command line interface to projector-installer"""
from os import path
# from os.path import expanduser, realpath, expandvars
from typing import Optional
import click
import typedparse  # type: ignore

from . import global_config
from .global_config import init_config_dir, init_cache_dir, get_changelog_url

from .actions import do_install_app, do_uninstall_app, do_find_app, do_list_app, do_run_config, \
    do_list_config, do_show_config, do_add_config, do_remove_config, do_edit_config, \
    do_rename_config, do_rebuild_config, do_install_cert
from .license import display_license
from .updates import get_latest_installer_version, SHORT_NETWORK_TIMEOUT, LONG_NETWORK_TIMEOUT, \
    is_newer_than_current
from .version import __version__


def is_first_start() -> bool:
    """Detects first app start."""
    return not path.isdir(global_config.config_dir)


def check_for_updates() -> None:
    """Check if new projector version is available"""
    pypi_version = get_latest_installer_version(timeout=SHORT_NETWORK_TIMEOUT)

    if pypi_version is None:
        click.echo('Checking for updates ... ', nl=False)
        pypi_version = get_latest_installer_version(timeout=LONG_NETWORK_TIMEOUT)
        click.echo('done.')

        if pypi_version is None:
            return

    if is_newer_than_current(pypi_version):
        msg = f'\nNew version {pypi_version} of projector-installer is available ' \
              f'(ver. {__version__} is installed)!\n' \
              f'Changelog: {get_changelog_url(pypi_version)}\n' \
              f'To update use command: pip3 install projector-installer --upgrade\n'
        click.echo(click.style(msg, bold=True))


# noinspection PyMethodMayBeStatic
# pylint: disable=C0103
class config:
    """
    Configuration management commands
    """

    def run(self, config_name: str = '', run_browser: Optional[bool] = True) -> None:
        """Run given configuration

        :param config_name: config name pattern to run
        :param run_browser: open projector URL in browser in WSL
        """
        do_run_config(config_name, run_browser)

    def list(self, config_name: str = '') -> None:
        """List run configurations whose names matches to the given pattern.
        If no pattern is given, lists all the configurations.

        :param config_name: config name pattern to list
        """
        do_list_config(config_name)

    def show(self, config_name: str = '') -> None:
        """Show existing configuration info

        :param config_name: config name pattern to show
        """
        do_show_config(config_name)

    def add(self, config_name: str,
            ide_path: Optional[str] = None,
            quick: Optional[bool] = False) -> None:
        """Add a new configuration

        :param config_name: name hint for new config
        :param ide_path: path to IDE to be used in new config (optional)
        :param quick: Quick mode - select IDE only
        """
        do_add_config(config_name, ide_path, quick)

    def remove(self, config_name: str = '') -> None:
        """Remove an existing configuration

        :param config_name: config name to remove
        """
        do_remove_config(config_name)

    def edit(self, config_name: str = '') -> None:
        """Change an existing configuration

        :param config_name: config name to edit
        """
        do_edit_config(config_name)

    def rename(self, from_name: str, to_name: str) -> None:
        """Rename an existing configuration

        :param from_name: original config name
        :param to_name: new config name
        """
        do_rename_config(from_name, to_name)

    def rebuild(self, config_name: str = '') -> None:
        """Regenerate all files related to given config

        :param config_name: config name to regenerate
        """
        do_rebuild_config(config_name)


# noinspection PyMethodMayBeStatic
class ide:
    """
    JetBrains IDEs management commands
    """

    def find(self, ide_name: str = '') -> None:
        """Find available IDE to install

        :param ide_name: ide name pattern to find
        """
        do_find_app(ide_name)

    def install(self, ide_name: str = '',
                no_auto_run: Optional[bool] = False,
                allow_updates: Optional[bool] = False,
                run_browser: Optional[bool] = True,
                quick: Optional[bool] = False) -> None:
        """Select and install IDE

        :param ide_name: ide name pattern to install
        :param no_auto_run: disable start IDE after install
        :param allow_updates: do not switch off IDE updates
        :param run_browser: auto open projector in browser (in WSL environment only)
        :param quick: Quick mode - select IDE only
        """
        do_install_app(ide_name, not no_auto_run, allow_updates, run_browser, quick)

    def uninstall(self, ide_name: str = '') -> None:
        """Select and uninstall IDE

        :param ide_name: ide name pattern to uninstall
        """
        do_uninstall_app(ide_name)

    def list(self, ide_name: str = '') -> None:
        """List installed IDE matches to given pattern

        :param ide_name: ide name ide name pattern to list
        """
        do_list_app(ide_name)


def find(ide_name: str = '') -> None:
    """Find available IDE to install

    :param ide_name: ide name pattern to find
    """
    do_find_app(ide_name)


def run(config_name: str = '', run_browser: Optional[bool] = True) -> None:
    """Run given configuration

    :param config_name: config name pattern to run
    :param run_browser: open projector URL in browser in WSL
    """
    do_run_config(config_name, run_browser)


def install(ide_name: str = '',
            no_auto_run: Optional[bool] = False,
            allow_updates: Optional[bool] = False,
            run_browser: Optional[bool] = True,
            quick: Optional[bool] = False) -> None:
    """Select and install IDE

    :param ide_name: ide name pattern to install
    :param no_auto_run: do not start IDE after install
    :param allow_updates: do not switch off IDE updates
    :param run_browser: auto open projector in browser (in WSL environment only)
    :param quick: Quick mode - select IDE only
    """
    do_install_app(ide_name, not no_auto_run, allow_updates, run_browser, quick)


def install_certificate(config_name: str = '',
                        certificate: Optional[str] = None,
                        key: Optional[str] = None,
                        chain: Optional[str] = None) -> None:
    """Install SSL certificate to run config
    Generates certificate automatically if no certificate is given

    :param config_name: run config name to install certificate
    :param certificate: PEM file with certificate
    :param key: PEM file with private key for certificate
    :param chain: PEM file with key chain for certificate (optional)
    """
    do_install_cert(config_name, certificate, key, chain)


def version() -> None:
    """Print installer version and exit"""
    print(f'projector installer version: {__version__}')


def projector() -> None:
    """
    This script helps to install, manage, and run JetBrains IDEs with Projector.
    """

    check_for_updates()

    # global_config.config_dir = realpath(expandvars(expanduser(config_directory)))
    #
    # if cache_directory:
    #     global_config.cache_dir = realpath(expandvars(expanduser(cache_directory)))

    if is_first_start():
        display_license()
        init_config_dir()
        do_install_app(None, auto_run=True, allow_updates=False, run_browser=True)
    else:
        init_cache_dir()
        typedparse.parse([version, find, run, install, install_certificate, ide(), config()])
