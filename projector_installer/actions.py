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
"""Real actions performed by projector script."""

from os import path, system, uname

import shutil
import signal
import subprocess
import sys

from requests import HTTPError
import click

from .apps import get_compatible_apps, get_app_path, get_installed_apps, get_product_info, \
    unpack_app

from .utils import download_file

from .dialogs import select_compatible_app, select_app_path, select_new_config_name, list_configs, \
    find_apps, select_http_port, select_projector_port, edit_config, list_apps, \
    select_installed_app, select_run_config, select_http_address

from .global_config import HTTP_DIR, get_download_cache_dir
from .http_server_process import HttpServerProcess
from .ide_configuration import install_projector_markdown_for, forbid_updates_for
from .run_config import get_run_configs, RunConfig, get_run_script, validate_run_config, \
    save_config, delete_config, rename_config, make_config_name, get_configs_with_app


def do_list_config(pattern=None):
    """Displays existing run configs names."""
    list_configs(pattern)


def do_show_config(config_name=None):
    """Shows details on run config.
    If given config name does not match unique config, runs interactive
     procedure to select it.
    """
    config_name, run_config = select_run_config(config_name)
    print(f'Configuration: {config_name}')
    print(f'IDE path: {run_config.path_to_app}')
    print(f'HTTP address: {run_config.http_address}')
    print(f'HTTP port: {run_config.http_port}')
    print(f'Projector port: {run_config.projector_port}')

    product_info = get_product_info(run_config.path_to_app)
    print(f'Product info: {product_info.name}, '
          f'version={product_info.version}, '
          f'build={product_info.build_number}')


def is_wsl():
    """Returns True if script is run in WSL environment."""
    return uname().release.find('microsoft') != -1


def do_run_browser(url):
    """Starts default browser and opens provided url in WSL."""
    system(f'cmd.exe /c start {url} 2> /dev/null')


# noinspection PyShadowingNames
def do_run_config(config_name=None, run_browser=True):
    """Executes specified config. If given name does not specify
    config, runs interactive selection procedure."""
    config_name, run_config = select_run_config(config_name)

    print(f'Configuration name: {config_name}')
    run_script_name = get_run_script(config_name)

    if not path.isfile(run_script_name):
        print(f'Cannot find file {run_script_name}')
        print(f'To fix, try: projector config edit {config_name}')
        return

    http_process = HttpServerProcess(run_config.http_address, run_config.http_port, HTTP_DIR,
                                     run_config.projector_port)

    def signal_handler(*args):
        # pylint: disable=unused-argument
        if http_process and http_process.is_alive():
            http_process.terminate()

        print('\nExiting...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    http_process.start()
    access_url = f'http://{run_config.http_address}:{run_config.http_port}/'
    print(f'HTTP process PID={http_process.pid}')
    print(f'To access your IDE, open {access_url} in your browser')
    print('Exit IDE or press Ctrl+C to stop Projector.')

    projector_process = subprocess.Popen([f'{run_script_name}'], stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)

    if run_browser:
        if is_wsl() and run_config.http_address == 'localhost':
            do_run_browser(access_url)

    projector_process.wait()

    print('Exiting...')

    if http_process and http_process.is_alive():
        http_process.terminate()


def make_run_config(app_path=None):
    """Creates run config with specified app_path."""
    if app_path is None:
        app_path = select_app_path()

    if app_path is None:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    http_address = select_http_address('localhost')
    http_port = select_http_port()
    projector_port = select_projector_port()

    return RunConfig(app_path, '', projector_port, http_address, http_port)


def do_add_config(config_name, app_path=None, auto_run=False, run_browser=True):
    """Adds new run config. If auto_run = True, runs it without questions.
    Asks user otherwise.
    """
    config_name = select_new_config_name(config_name)

    if config_name is None:
        print('Configuration name was not selected, exiting...')
        sys.exit(1)

    run_config = make_run_config(app_path)

    if run_config.path_to_app is None:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    try:
        validate_run_config(run_config)
    except IsADirectoryError as exception:
        print(f'Wrong configuration parameters: {str(exception)}, exiting ...')
        sys.exit(1)

    save_config(config_name, run_config)

    do_run = True if auto_run else click.prompt('Would you like to run new config? [y/n]',
                                                type=bool)

    if do_run:
        do_run_config(config_name, run_browser)


def do_remove_config(config_name=None):
    """Selects (if necessary) and removes selected run config."""
    config_name, _ = select_run_config(config_name)
    print(f'Removing configuration {config_name}')
    delete_config(config_name)
    print('done.')


def do_edit_config(config_name=None):
    """Selects (if necessary) and edits selected run config."""
    config_name, run_config = select_run_config(config_name)
    print(f'Edit configuration {config_name}')
    run_config = edit_config(run_config)

    try:
        validate_run_config(run_config)
    except IsADirectoryError as exception:
        print(f'Wrong configuration parameters: {str(exception)}, exiting ...')
        sys.exit(1)

    save_config(config_name, run_config)

    print('done.')


def do_rename_config(from_name, to_name):
    """Renames run config."""
    run_configs = get_run_configs()

    if from_name not in run_configs:
        print(f'Configuration name {from_name} does not exist, exiting...')
        sys.exit(1)

    if from_name == to_name:
        print('Cannot rename configuration to the same name, exiting...')
        sys.exit(1)

    if to_name in run_configs:
        print(f'Cannot rename to {to_name} - the configuration already exists, exiting...')
        sys.exit(1)

    rename_config(from_name, to_name)


def do_find_app(pattern=None):
    """Prints known projector-compatible apps."""
    find_apps(pattern)


def do_list_app(pattern=None):
    """Prints apps installed by projector."""
    list_apps(pattern)


def do_install_app(app_name, auto_run=False, allow_updates=False, run_browser=True):
    """Installs specified app."""
    apps = get_compatible_apps(app_name)

    if len(apps) == 0:
        print('There are no known IDEs matched to the given name.')
        if app_name is None:
            print('Try to reinstall Projector.')
        print('Exiting...')
        sys.exit(1)

    if len(apps) > 1:
        app_name = select_compatible_app(app_name)

        if app_name is None:
            print('IDE was not selected, exiting...')
            sys.exit(1)
    else:
        app_name = apps[0].name

    apps = get_compatible_apps(app_name)
    app = apps[0]

    print(f'Installing {app.name}')

    try:
        path_to_dist = download_file(app.url, get_download_cache_dir())
    except HTTPError as http:
        print(f'Unable to download a file, try again later: {str(http)}. Exiting ...')
        sys.exit(1)
    except IOError as error:
        print(f'Unable to write downloaded file, try again later: {str(error)}. Exiting ...')
        sys.exit(1)

    try:
        app_name = unpack_app(path_to_dist)
    except IOError as error:
        print(f'Unable to extract the archive: {str(error)}. Exiting...')
        sys.exit(1)

    config_name = make_config_name(app_name)
    app_path = get_app_path(app_name)
    install_projector_markdown_for(app_path)

    if not allow_updates:
        forbid_updates_for(app_path)

    print('done.')
    do_add_config(config_name, app_path, auto_run, run_browser)


def do_uninstall_app(app_name=None):
    """Uninstalls specified app."""
    apps = get_installed_apps(app_name)

    if len(apps) == 0:
        print('There are no installed apps matched the given name. Exiting...')
        sys.exit(1)

    if len(apps) > 1:
        app_name = select_installed_app(app_name)
    else:
        app_name = apps[0]

    if app_name is None:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    configs = get_configs_with_app(app_name)

    if configs:
        print(f'Unable to uninstall {app_name} - there are configurations with this IDE:')
        for config in configs:
            print(config)
        print('Try to remove configurations first. Exiting...')
        sys.exit(1)

    print(f'Uninstalling {app_name}')
    app_path = get_app_path(app_name)
    shutil.rmtree(app_path)
    print('done.')
