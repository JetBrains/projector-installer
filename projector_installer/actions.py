# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.

"""Real actions performed by projector script."""
import os
import shutil
import signal
import subprocess
import sys
from os import path, system, uname, remove
from os.path import isfile
from typing import Optional, List

from .apps import get_app_path, get_installed_apps, get_product_info, \
    get_java_path, get_path_to_latest_app, is_valid_app_path, is_toolbox_path, \
    download_and_install
from .certificate_chain import get_certificate_chain
from .global_config import LONG_NETWORK_TIMEOUT
from .ide_update import is_updatable_ide, get_update, update_config, check_ide_update, is_tested_ide
from .log_utils import init_log, shutdown_log, get_path_to_log
from .secure_config import get_ca_crt_file, parse_custom_names

from .utils import get_java_version, get_local_addresses

from .dialogs import select_app, select_new_config_name, list_configs, \
    find_apps, edit_config, list_apps, select_installed_app, select_run_config, make_run_config, \
    get_user_install_input, get_quick_config, select_app_path

from .run_config import RunConfig, get_run_configs, get_run_script_path, validate_run_config, \
    delete_config, rename_config, make_config_name, get_configs_with_app, \
    lock_config, release_config, make_config_name_from_path

from .config_generator import save_config, check_config


def do_list_config(pattern: Optional[str] = None) -> None:
    """Displays existing run configs names."""
    list_configs(pattern)


def do_show_config(pattern: Optional[str] = None) -> None:
    """Shows details on run config.
    If given config name does not match unique config, runs interactive
     procedure to select it.
    """
    run_config = select_run_config(pattern)
    print(f'Configuration: {run_config.name}')
    print(f'IDE path: {run_config.path_to_app}')
    print(f'Projector port: {run_config.projector_port}')

    product_info = get_product_info(run_config.path_to_app)
    print(f'Product info: {product_info.name}, '
          f'version={product_info.version}, '
          f'build={product_info.build_number}')

    if run_config.toolbox:
        print('Toolbox config = yes')

    if run_config.is_secure():
        print('Secure config = yes')

    if run_config.is_password_protected():
        print(f'RW Password: = {run_config.password}')
        print(f'RO Password: = {run_config.ro_password}')


def is_wsl() -> bool:
    """Returns True if script is run in WSL environment."""
    return uname().release.find('microsoft') != -1


def do_run_browser(url: str) -> None:
    """Starts default browser and opens provided url in WSL."""
    system(f'cmd.exe /c start {url} 2> /dev/null')


def wsl_warning() -> None:
    """Show warning for WSL environment."""
    print('It seems that you are using WSL environment.')
    print('WSL is still experimental technology, and if you experience any issues accessing '
          'projector from browser please refer to Projector README file: '
          'https://github.com/JetBrains/projector-installer#resolving-wsl-issues')


def get_access_urls(run_config: RunConfig) -> List[str]:
    """Returns access URLs for given config"""

    schema = 'http'

    if run_config.is_secure():
        schema = 'https'

    urls = []

    if run_config.custom_names:
        addresses = parse_custom_names(run_config.custom_names)
    else:
        addresses = get_local_addresses()

        if '127.0.0.1' in addresses:
            addresses = ['localhost'] + addresses

    for address in addresses:
        urls.append(f'{schema}://{address}:{run_config.projector_port}/index.html')

    if run_config.password:
        res = list(map(lambda x: x + "?token=" + run_config.password, urls))

        if run_config.password != run_config.ro_password:
            res += list(map(lambda x: x + "?token=" + run_config.ro_password, urls))

        urls = res

    return urls


def is_compatible_java(app_path: str) -> bool:
    """Checks bundled java version compatibility."""
    java_path = get_java_path(app_path)
    version = get_java_version(java_path)
    return version.startswith('11.')


def regenerate_config_if_toolbox(run_config: RunConfig) -> RunConfig:
    """Regenerates toolbox run config to run latest available IDE in channel """

    if run_config.toolbox:
        path_to_app = get_path_to_latest_app(run_config.path_to_app)

        if path_to_app:
            run_config.path_to_app = path_to_app
            save_config(run_config)

    return run_config


PROJECTOR_PID = None


def do_run_config(config_name: Optional[str] = None, run_browser: bool = True) -> None:
    """Executes specified config. If given name does not specify
    config, runs interactive selection procedure."""
    run_config = select_run_config(config_name)

    print(f'Configuration name: {run_config.name}')
    check_ide_update(run_config)

    run_config = regenerate_config_if_toolbox(run_config)
    run_script_name = get_run_script_path(run_config.name)

    if not path.isfile(run_script_name):
        print(f'Cannot find file {run_script_name}')
        print(f'To fix, try: projector config edit {run_config.name}')
        sys.exit(1)

    lock = lock_config(run_config.name)

    if not lock:
        print(f'Configuration {run_config.name} is already in use. Exiting...')
        sys.exit(1)

    if not check_config(run_config):
        print("WARNING: run config may not correspond to autogenerated files.\n"
              "Try run projector config rebuild\n")

    def signal_handler(*args):  # type: ignore
        # pylint: disable=unused-argument
        print('\nCtrl-C is pressed, exiting...')
        if PROJECTOR_PID:
            os.kill(PROJECTOR_PID, signal.SIGTERM)

    log_file = init_log(run_config.name)

    projector_process = subprocess.Popen([f'{run_script_name}'],
                                         stdout=log_file,
                                         stderr=log_file)

    global PROJECTOR_PID  # pylint: disable=global-statement
    PROJECTOR_PID = projector_process.pid
    signal.signal(signal.SIGINT, signal_handler)

    access_urls = get_access_urls(run_config)
    urls_string = "\n\t".join(access_urls)
    print(f'To access IDE, open in browser \n\t{urls_string}\n')
    print('To see Projector logs in realtime run\n\t'
          f'tail -f "{get_path_to_log(run_config.name)}"\n')

    if run_config.is_secure() and not run_config.certificate:
        print('If browser warns on unsecure connection, install projector certificate:')
        print(get_ca_crt_file())
        print('Refer to: ')
        print('https://github.com/JetBrains/projector-installer/blob/master/'
              'README.md#what-is-secure-connection')

    if not is_compatible_java(run_config.path_to_app):
        print('Bundled JVM is incompatible with Projector.')
        print('Current config may be nonfunctional.')

    print('Exit IDE or press Ctrl+C to stop Projector.')

    if run_browser:
        if is_wsl():
            wsl_warning()
            do_run_browser(access_urls[0])

    ret_code = projector_process.wait()
    shutdown_log(ret_code, log_file)
    release_config(lock)


def do_add_config(hint: Optional[str], app_path: Optional[str], quick: bool) -> None:
    """
    Adds new run config. If auto_run = True, runs it without questions.
    Asks user otherwise.
    """

    if quick:
        print('Creating config in quick mode; '
              'for full customization you can rerun this command '
              'with "--expert" argument or edit this config later '
              'via "projector config edit" command')

    app = app_path if app_path and is_valid_app_path(app_path) else select_app_path()

    if app is None:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    config_name_hint = hint if hint else make_config_name_from_path(app)

    if quick:
        run_config = get_quick_config(config_name_hint)
        run_config.path_to_app = app
        run_config.toolbox = is_toolbox_path(app)
    else:
        config_name = select_new_config_name(config_name_hint)

        if config_name is None:
            print('Configuration name was not selected, exiting...')
            sys.exit(1)

        run_config = make_run_config(config_name, app)

    if run_config.path_to_app is None:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    if run_config.toolbox:
        latest_app = get_path_to_latest_app(run_config.path_to_app)

        if latest_app is None:
            raise ValueError(f'Wrong toolbox path: {run_config.path_to_app}')

        run_config.path_to_app = latest_app

    try:
        validate_run_config(run_config)
    except ValueError as exception:
        print(f'Wrong configuration parameters: {str(exception)}, exiting ...')
        sys.exit(1)

    print(f'Adding new config with name {run_config.name}')

    save_config(run_config)


def do_remove_config(config_name: Optional[str] = None) -> None:
    """Selects (if necessary) and removes selected run config."""
    config_name = select_run_config(config_name).name

    lock = lock_config(config_name)

    if not lock:
        print(f'Configuration {config_name} is already in use. Exiting...')
        sys.exit(1)

    print(f'Removing configuration {config_name}')
    delete_config(config_name)
    release_config(lock)
    print('done.')


def do_edit_config(config_name: Optional[str] = None) -> None:
    """Selects (if necessary) and edits selected run config."""
    run_config = select_run_config(config_name)

    lock = lock_config(run_config.name)

    if not lock:
        print(f'Configuration {run_config.name} is already in use. Exiting...')
        sys.exit(1)

    print(f'Edit configuration {run_config.name}')

    run_config = edit_config(run_config)

    try:
        validate_run_config(run_config)
    except ValueError as exception:
        print(f'Wrong configuration parameters: {str(exception)}, exiting ...')
        sys.exit(1)

    save_config(run_config)
    release_config(lock)
    print('done.')


def do_rename_config(from_name: str, to_name: str) -> None:
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

    lock = lock_config(from_name)

    if not lock:
        print(f'Configuration {from_name} is already in use. Exiting...')
        sys.exit(1)

    rename_config(from_name, to_name)
    release_config(lock)


def do_rebuild_config(config_name: Optional[str] = None) -> None:
    """Regenerates all run config related files"""
    run_config = select_run_config(config_name)

    lock = lock_config(run_config.name)

    if not lock:
        print(f'Configuration {run_config.name} is already in use. Exiting...')
        sys.exit(1)

    print(f'Rebuild run config {run_config.name}')
    save_config(run_config)
    release_config(lock)


def do_update_config(config_name: Optional[str] = None, allow_update: bool = False) -> None:
    """Updates IDE in selected config if update is available"""
    run_config = select_run_config(config_name)

    if not is_updatable_ide(run_config.path_to_app):
        print(f'IDE {run_config.path_to_app} can\'t be updated by Projector. Exiting...')
        return

    print('Checking for updates.')
    product = get_update(run_config, timeout=LONG_NETWORK_TIMEOUT)
    current = get_product_info(run_config.path_to_app).name

    if product is None:
        msg = f'There are no updates for IDE {current}'
        if is_tested_ide(run_config):
            msg += ' in compatible IDE file.'
        else:
            msg += ' on release server.'

        print(msg, ' Exiting...')
        return

    lock = lock_config(run_config.name)

    if not lock:
        print(f'Configuration {run_config.name} is already in use. Exiting...')
        sys.exit(1)

    print(f'Updating IDE for run config {run_config.name}.')
    update_config(run_config, product, allow_update)
    print(f'{current} is updated to {product.name}')

    release_config(lock)


def do_install_cert(config_name: Optional[str], path_to_certificate: Optional[str],
                    path_to_key: Optional[str], path_to_chain: Optional[str]) -> None:
    """Installs user-specified certificate"""

    run_config = select_run_config(config_name)
    lock = lock_config(run_config.name)

    if not lock:
        print(f'Configuration {run_config.name} is already in use. Exiting...')
        sys.exit(1)

    print(f'Installing {path_to_certificate if path_to_certificate else "autogenerated"} '
          f'certificate to config {run_config.name}')

    if path_to_certificate is None:
        run_config.make_secure()
    else:
        if not isfile(path_to_certificate):
            print(f'Certificate file {path_to_certificate} does not exist. Exiting ...')
            sys.exit(1)

        if path_to_key is None or not isfile(path_to_key):
            print(f'Key file {path_to_key} does not exist. Exiting ...')
            sys.exit(1)

        if not path_to_chain:
            path_to_chain = get_certificate_chain(path_to_certificate)
            need_remove = isfile(path_to_chain)

        run_config.add_certificate(path_to_certificate, path_to_key, path_to_chain)

        if need_remove:
            remove(path_to_chain)

    save_config(run_config)

    release_config(lock)


def do_find_app(pattern: Optional[str] = None) -> None:
    """Prints known projector-compatible apps."""
    find_apps(pattern)


def do_list_app(pattern: Optional[str] = None) -> None:
    """Prints apps installed by projector."""
    list_apps(pattern)


def do_install_app(app_name: Optional[str], auto_run: bool = True, allow_updates: bool = False,
                   run_browser: bool = True, quick: bool = False) -> None:
    """Installs specified app."""

    if quick:
        print('Installing IDE in quick mode; '
              'for full customization you can rerun this command '
              'with "--expert" argument or edit this config later '
              'via "projector config edit" command')

    channel, app = select_app(app_name)

    if app is None:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    config_name_hint = make_config_name(app.name)

    if quick:
        run_config: Optional[RunConfig] = get_quick_config(config_name_hint)
    else:
        run_config = get_user_install_input(config_name_hint)

    if run_config is None:
        print('Config parameters was not specified, exiting ...')
        sys.exit(1)

    print(f'Installing {app.name}')
    run_config.update_channel = channel
    run_config.path_to_app = download_and_install(app.url, allow_updates)

    try:
        validate_run_config(run_config)
    except ValueError as exception:
        print(f'Wrong configuration parameters: {str(exception)}, exiting ...')
        sys.exit(1)

    save_config(run_config)

    if auto_run:
        do_run_config(run_config.name, run_browser)


def do_uninstall_app(app_name: Optional[str] = None) -> None:
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
