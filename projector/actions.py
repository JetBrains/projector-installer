import shutil
import signal
import subprocess
import sys
from os import path, uname, system

from .apps import get_compatible_apps, download_app, unpack_app, get_app_path, get_installed_apps, get_product_info

from .dialogs import select_known_app, select_config_name, select_app_path, select_new_config_name, list_configs, \
    find_apps, select_http_port, select_projector_port, edit_config, list_apps, select_installed_app
from .global_config import HTTP_DIR
from .http_server_process import HttpServerProcess
from .markdown import install_projector_markdown
from .run_config import get_run_configs, RunConfig, get_run_script, validate_run_config, save_config, \
    delete_config, rename_config, make_config_name, get_configs_with_app


def do_list_config(pattern=None):
    list_configs(pattern)


def do_show_config(config_name=None):
    run_configs = get_run_configs(config_name)

    if len(run_configs) == 0:
        print(f'Configuration name {config_name} is unknown, exiting...')
        sys.exit(1)

    if len(run_configs) > 1:
        config_name = select_config_name(config_name)

        if config_name is None:
            print('Configuration was not selected, exiting...')
            sys.exit(1)
    else:
        config_name = list(run_configs.keys())[0]

    run_config = run_configs[config_name]
    print(f"Configuration: {config_name}")
    print(f"IDE path: {run_config.path_to_app}")
    print(f"HTTP address: {run_config.http_address}")
    print(f"HTTP port: {run_config.http_port}")
    print(f"Projector port: {run_config.projector_port}")

    product_info = get_product_info(run_config.path_to_app)
    print(f"Product info: {product_info.name}, version={product_info.version}, build={product_info.build_number}")


# noinspection PyShadowingNames
def do_run_config(config_name=None):
    run_configs = get_run_configs(config_name)

    if len(run_configs) == 0:
        print(f'Configuration matched to {config_name} was not found, exiting...')
        sys.exit(1)

    if len(run_configs) == 1:
        config_name = list(run_configs.keys())[0]
    else:
        config_name = select_config_name(config_name)

        if config_name is None:
            print('A configuration is not selected, exiting...')
            sys.exit(1)

    if config_name not in run_configs:
        print(f'Configuration name {config_name} is unknown, exiting...')
        return

    print(f"Configuration name: {config_name}")
    run_config = run_configs[config_name]

    run_script_name = get_run_script(config_name)

    if not path.isfile(run_script_name):
        print(f"Cannot find file {run_script_name}")
        print(f"To fix, try: projector config edit {config_name}")
        return

    http_process = HttpServerProcess(run_config.http_address, run_config.http_port, HTTP_DIR, run_config.projector_port)

    def signal_handler(*args):
        if http_process and http_process.is_alive():
            http_process.terminate()

        print('\nExiting...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    http_process.start()
    access_url = f'http://{run_config.http_address}:{run_config.http_port}/'
    print(f"HTTP process PID={http_process.pid}")
    print(f"To access your IDE, open {access_url} in your browser")
    print('Exit IDE or press Ctrl+C to stop Projector.')

    # if uname().release.find('microsoft') != -1:  # wsl
    #     system(f'cmd.exe /c start {access_url}')

    subprocess.call([f"{run_script_name}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if http_process and http_process.is_alive():
        http_process.terminate()


def make_run_config(app_path=None):
    if app_path is None:
        app_path = select_app_path()

    if app_path is None:
        print("IDE was not selected, exiting...")
        sys.exit(1)

    http_port = select_http_port()
    projector_port = select_projector_port()

    return RunConfig(app_path, "", projector_port, "localhost", http_port)


def do_add_config(config_name, app_path=None):
    config_name = select_new_config_name(config_name)

    if config_name is None:
        print("Configuration name was not selected, exiting...")
        sys.exit(1)

    run_config = make_run_config(app_path)

    if run_config.path_to_app is None:
        print("IDE was not selected, exiting...")
        sys.exit(1)

    try:
        validate_run_config(run_config)
    except Exception as e:
        print(f"Wrong configuration parameters: {str(e)}, exiting ...")
        sys.exit(1)

    save_config(config_name, run_config)


def do_remove_config(config_name=None):
    run_configs = get_run_configs(config_name)

    if len(run_configs) == 0:
        if config_name:
            print(f"There are no configurations with a name matched to {config_name}")
        else:
            print(f"There are no configurations.")

        print("exiting...")
        sys.exit(1)

    if len(run_configs) > 1 or config_name is None:
        config_name = select_config_name(config_name)

        if config_name is None:
            print('Configuration is not selected, existing...')
            return
    else:
        config_name = list(run_configs.keys())[0]

    if config_name not in run_configs:
        print(f'Configuration name {config_name} is unknown, existing...')
        return

    print(f"Removing configuration {config_name}")
    delete_config(config_name)
    print("done.")


def do_edit_config(config_name=None):
    run_configs = get_run_configs(config_name)

    if len(run_configs) == 0:
        print(f'Configuration name {config_name} is unknown, existing...')
        sys.exit(1)

    if len(run_configs) > 1:
        config_name = select_config_name(config_name)
    else:
        config_name = list(run_configs.keys())[0]

    if config_name is None:
        print('Configuration is not selected, existing...')
        sys.exit(1)

    run_config = run_configs[config_name]

    print(f"Edit configuration {config_name}")

    run_config = edit_config(run_config)

    try:
        validate_run_config(run_config)
    except Exception as e:
        print(f"Wrong configuration parameters: {str(e)}, exiting ...")
        sys.exit(1)

    save_config(config_name, run_config)

    print("done.")


def do_rename_config(from_name, to_name):
    run_configs = get_run_configs()

    if from_name not in run_configs:
        print(f"Configuration name {from_name} does not exist, exiting...")
        sys.exit(1)

    if from_name == to_name:
        print(f"Cannot rename configuration to the same name, exiting...")
        sys.exit(1)

    if to_name in run_configs:
        print(f"Cannot rename to {to_name} - the configuration already exists, exiting...")
        sys.exit(1)

    rename_config(from_name, to_name)


########################## Apps actions

def do_find_app(pattern=None):
    find_apps(pattern)


def do_list_app(pattern=None):
    list_apps(pattern)


def do_install_app(app_name):
    apps = get_compatible_apps(app_name)

    if len(apps) == 0:
        print("There are no known IDEs matched to the given name.")
        if app_name is None:
            print("Try to reinstall Projector.")
        print("Exiting...")
        sys.exit(1)

    if len(apps) > 1:
        app_name = select_known_app(app_name)

        if app_name is None:
            print("IDE was not selected, exiting...")
            sys.exit(1)
    else:
        app_name = apps[0].name

    apps = get_compatible_apps(app_name)
    app = apps[0]

    print(f"Installing {app.name}")

    try:
        path_to_dist = download_app(app.url)
    except Exception as e:
        print(f"Unable to download a file, try again later: {str(e)}. Exiting ...")
        sys.exit(1)

    try:
        app_name = unpack_app(path_to_dist)
    except Exception as e:
        print(f"Unable to extract the archive: {str(e)}. Exiting...")
        sys.exit(1)

    config_name = make_config_name(app_name)
    app_path = get_app_path(app_name)

    do_add_config(config_name, app_path)

    install_projector_markdown(app_path)

    print("done.")


def do_uninstall_app(app_name=None):
    apps = get_installed_apps(app_name)

    if len(apps) == 0:
        print("There are no installed apps matched the given name. Exiting...")
        sys.exit(1)

    if len(apps) > 1:
        app_name = select_installed_app(app_name)
    else:
        app_name = apps[0]

    if app_name is None:
        print("IDE was not selected, exiting...")
        sys.exit(1)

    configs = get_configs_with_app(app_name)

    if configs:
        print(f"Unable to uninstall {app_name} - there are configurations with this IDE:")
        for c in configs:
            print(c)
        print("Try to remove configurations first. Exiting...")
        sys.exit(1)

    print(f"Uninstalling {app_name}")
    p = get_app_path(app_name)
    shutil.rmtree(p)
    print("done.")
