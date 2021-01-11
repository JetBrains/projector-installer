# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""User dialog related procedures."""

import sys
import readline
from os.path import expanduser
from typing import Optional, Dict, List, Tuple, TypeVar, Callable
from dataclasses import dataclass

import click

from .run_config import get_run_configs, RunConfig, get_run_config_names, get_used_projector_ports
from .apps import get_installed_apps, get_app_path, is_path_to_app, is_toolbox_path
from .secure_config import generate_token
from .utils import get_local_addresses
from .products import get_compatible_apps, IDEKind, Product, get_all_apps

DEF_PROJECTOR_PORT: int = 9999


def get_compatible_app_names(kind: IDEKind, pattern: Optional[str] = None) -> List[Product]:
    """Get sorted list of projector-compatible applications, matches given pattern."""
    res = get_compatible_apps(kind, pattern)
    return sorted(res, key=lambda x: x.name)


def display_run_configs_names(config_names: List[str]) -> None:
    """Pretty-print config names."""
    for i, config_name in enumerate(config_names):
        print(f'\t{i + 1:4}. {config_name}')


def list_configs(pattern: Optional[str] = None) -> None:
    """Displays names of run configs, matches to pattern."""
    config_names = get_run_config_names(pattern)
    display_run_configs_names(config_names)


def display_run_configs(run_configs: Dict[str, RunConfig]) -> None:
    """Display sorted names of given run configs."""
    config_names = list(run_configs.keys())
    config_names.sort()
    display_run_configs_names(config_names)


def print_selection_list(names: List[str]) -> None:
    """Pretty list for selection."""
    for i, name in enumerate(names):
        print(f'\t{i + 1:4}. {name}')


def list_apps(pattern: Optional[str]) -> None:
    """Print list of installed apps"""
    apps = get_installed_apps(pattern)
    print_selection_list(apps)


T = TypeVar('T', IDEKind, Product, str)  # pylint: disable=C0103


def select_from_list(data: List[T], name: Callable[[T], str], prompt: str) -> Optional[T]:
    """Interactively selects named entity from given list"""
    names: List[str] = list(map(name, data))
    prompt = f'{prompt}: [0-{len(names)}]'

    while True:
        print_selection_list(names)
        pos: int = click.prompt(prompt, type=int)

        if pos < 0 or pos > len(names):
            print('Invalid number.')
            continue

        if pos == 0:
            return None

        return data[pos - 1]


def select_installed_app(pattern: Optional[str] = None) -> Optional[str]:
    """Interactively selects installed ide."""
    return select_from_list(get_installed_apps(pattern), lambda it: it,
                            'Choose an IDE number to uninstall or 0 to exit')


def select_ide_kind() -> Optional[IDEKind]:
    """Interactively selects desired IDE kind"""
    kinds = [k for k in IDEKind if k != IDEKind.Unknown]
    return select_from_list(kinds, lambda it: it.name, 'Choose IDE type or 0 to exit')


def get_app_list(kind: IDEKind, pattern: Optional[str] = None) -> List[Product]:
    """Returns compatible or full app list, depending on user choice"""
    compatible = click.prompt('Do you want to use Projector-compatible IDE only? [y/n]',
                              type=bool)
    return get_compatible_app_names(kind, pattern) if compatible else get_all_apps(kind, pattern)


def find_apps(pattern: Optional[str] = None) -> None:
    """Pretty-print projector-compatible applications, matched to given pattern."""
    kind = select_ide_kind()

    if kind is None:
        print('No app kind selected, exiting...')
        sys.exit(2)

    apps = get_app_list(kind, pattern)
    print_selection_list(list(map(lambda x: x.name, apps)))


def select_app(pattern: Optional[str] = None) -> Optional[Product]:
    """Interactively selects app name from list of projector-compatible applications."""
    kind = select_ide_kind()

    if kind is None:
        return None

    apps = get_app_list(kind, pattern)

    return select_from_list(apps, lambda it: it.name, 'Choose IDE number to install or 0 to exit')


def select_unused_config_name(hint: str) -> str:
    """Generate unused config name."""
    run_configs = get_run_configs()
    cnt = 0
    res = hint

    while res in run_configs:
        cnt += 1
        res = f'{hint}_{cnt}'

    return res


def select_new_config_name(hint: Optional[str]) -> Optional[str]:
    """Prompts for new config name and checks for collisions."""
    run_config = get_run_configs()

    if hint:
        hint = select_unused_config_name(hint)
        prompt = 'Enter a new configuration name or press ENTER for default'
    else:
        prompt = 'Enter a new configuration name'

    while True:
        name: str = click.prompt(prompt, default=hint)

        if not name:
            return None

        if name in run_config:
            print(f'A configuration with name {name} already exists, please choose another name.')
            print('The known configurations:')
            list_configs()
            continue

        return name


def select_run_config(config_name: Optional[str]) -> RunConfig:
    """Interactively select run config."""
    run_configs: Dict[str, RunConfig] = get_run_configs(config_name)

    if len(run_configs) == 0:
        print(f'Configuration with name {config_name} is unknown, exiting...')
        sys.exit(1)

    if len(run_configs) > 1:
        while True:
            display_run_configs(run_configs)
            prompt = f'Choose a configuration number or 0 to exit: [0-{len(run_configs)}]'
            config_number = click.prompt(prompt, type=int)

            if config_number < 0 or config_number > len(run_configs):
                print('Invalid number selected.')
                continue

            if config_number == 0:
                print('Configuration was not selected, exiting...')
                sys.exit(1)
            else:
                config_names = get_run_config_names(config_name)
                name = config_names[config_number - 1]
                return run_configs[name]

    return list(run_configs.values())[0]


def select_installed_app_path() -> Optional[str]:
    """Selects installed app and returns path to it."""
    apps = get_installed_apps()
    res = select_from_list(apps, lambda it: it, 'Choose IDE number to install or 0 to exit')
    return res if res is None else get_app_path(res)


def is_valid_app_path(app_path: str) -> bool:
    """Checks if entered app path is valid"""
    return is_path_to_app(app_path) or is_toolbox_path(app_path)


def select_manual_app_path(default: str = '') -> str:
    """Prompts for path to ide."""
    readline.set_completer_delims(' \t\n=')
    readline.parse_and_bind("tab: complete")

    if default:
        prompt = f'Enter the path to IDE (default: {default}, <tab> for complete): '
    else:
        prompt = 'Enter the path to IDE (<tab> for complete): '

    while True:
        path: str = input(prompt)

        if len(path) == 0 and default:
            path = default

        if len(path) > 0:
            path = expanduser(path)

        if is_valid_app_path(path):
            return path

        click.echo(f'Path {path} does not looks like a valid path.')


def select_app_path() -> Optional[str]:
    """Select path to ide."""
    apps = get_installed_apps()

    if apps:
        inst = click.prompt('Do you want to choose a Projector-installed IDE? [y/n]', type=bool)

        if inst:
            return select_installed_app_path()

        return select_manual_app_path()

    enter = click.prompt('There are no installed Projector IDEs.\nWould you like to specify '
                         'a path to IDE manually?',
                         type=bool)
    if enter:
        return select_manual_app_path()

    return None


def get_all_listening_ports() -> List[int]:
    """
    Returns all tcp port numbers in LISTEN state (on any address).
    Reads port state from /proc/net/tcp.
    """
    res = []

    with open('/proc/net/tcp', 'r') as file:
        try:
            next(file)
            for line in file:
                split_line = line.strip().split(' ')
                hex_port = split_line[1].split(':')[1]
                hex_state = split_line[3]

                if hex_state == '0A':
                    res.append(int(hex_port, 16))
        except StopIteration:
            pass

    return res


def is_open_port(port: int) -> bool:
    """ Checks if tcp port is LISTEN state in system."""
    return port in get_all_listening_ports()


def get_def_port(ports: List[int], default: int) -> int:
    """Returns default or first unused in system and in run configs port."""
    port = default

    if len(ports) > 0:
        ports.sort()
        port = ports[-1] + 1

    while is_open_port(port):
        port += 1

    return port


def get_def_projector_port() -> int:
    """Returns unused port for projector server."""
    ports = get_used_projector_ports()
    return get_def_port(ports, DEF_PROJECTOR_PORT)


def get_all_addresses() -> List[str]:
    """Returns list of acceptable ip addresses."""
    return ['localhost', '0.0.0.0'] + get_local_addresses()


def check_listening_address(address: str) -> bool:
    """Check entered ip address for validity."""
    return address in get_all_addresses()


def select_projector_port() -> int:
    """Selects port for projector server."""
    port = get_def_projector_port()
    res: int = click.prompt('Enter a desired Projector port (press ENTER for default)',
                            default=str(port))
    return res


def select_password(prompt: str, default: str = '') -> str:
    """Prompts for password if needed """
    password: str = click.prompt(text=prompt, default=default, hide_input=True,
                                 confirmation_prompt=True)

    return password


def select_password_pair(def_password: str = '', def_ro_password: str = '') -> Tuple[str, str]:
    """Prompts for pair of access passwords if needed"""
    password = ''
    ro_password = ''
    need_password = click.prompt('Would you like to set password for connection? [y/n]',
                                 type=bool)

    if need_password:
        password = select_password('Please specify RW password:', default=def_password)

        need_ro_password = click.prompt('Would you like to set separate read-only password? [y/n]',
                                        type=bool)

        if need_ro_password:
            ro_password = select_password('Please specify RO password:', default=def_ro_password)
        else:
            ro_password = password

    return password, ro_password


def select_custom_names(default: str = '') -> str:
    """Asks user for custom domains to be added to certificate"""
    use_custom_names = click.prompt('Would you like to specify custom names for certificate? [y/n]',
                                    type=bool)

    custom_names: str = click.prompt('Please specify the comma-separated list of custom names',
                                     default=default,
                                     type=str) if use_custom_names else ''

    return custom_names


def edit_config(config: RunConfig) -> RunConfig:
    """Edits existing config."""
    config.path_to_app = select_manual_app_path(default=config.path_to_app)
    config.toolbox = False

    if is_toolbox_path(config.path_to_app):
        config.toolbox = click.prompt(
            'App path looks like path to ToolBox managed app. '
            'Would you like to use latest app from this channel? [y/n]',
            type=bool)

    config.projector_port = click.prompt('Enter a Projector port (press ENTER for default)',
                                         default=str(config.projector_port))

    secure_config = click.prompt(
        'Use secure connection '
        '(this option requires installing a projector\'s certificate to browser)? [y/n]',
        type=bool)

    config.token = generate_token() if secure_config else ''
    config.custom_names = select_custom_names(config.custom_names)
    config.password, config.ro_password = select_password_pair(config.password, config.ro_password)

    return config


def make_run_config(config_name: str, app_path: Optional[str] = None) -> RunConfig:
    """Creates run config with specified app_path."""
    if app_path is None:
        app_path = select_app_path()

    if not app_path:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    is_toolbox = False

    if is_toolbox_path(app_path):
        is_toolbox = click.prompt(
            'App path looks like path to ToolBox managed app. '
            'Would you like to use latest app from this channel? [y/n]',
            type=bool)

    projector_port = select_projector_port()
    secure_config = click.prompt(
        'Use secure connection '
        '(this option requires installing a projector\'s certificate to browser)? [y/n]',
        type=bool)
    token = generate_token() if secure_config else ''
    custom_names = select_custom_names()
    password, ro_password = select_password_pair()

    return RunConfig(config_name, expanduser(app_path), projector_port,
                     token, password, ro_password, is_toolbox, custom_names)


@dataclass
class UserInstallInput:
    """Represents user answers during install session"""

    # pylint: disable=too-many-instance-attributes
    config_name: str
    projector_port: int
    do_run: bool
    secure_config: bool
    password: str
    ro_password: str
    custom_names: str


def get_user_install_input(config_name_hint: str, auto_run: bool) -> Optional[UserInstallInput]:
    """Interactively creates user input"""
    config_name = select_new_config_name(config_name_hint)

    if not config_name:
        return None

    projector_port = select_projector_port()
    do_run = True if auto_run else click.prompt('Would you like to run installed ide? [y/n]',
                                                type=bool)

    secure_config = click.prompt(
        'Use secure connection '
        '(this option requires installing a projector\'s certificate to browser)? [y/n]',
        type=bool)

    custom_names = select_custom_names()

    password, ro_password = select_password_pair()

    return UserInstallInput(config_name, projector_port,
                            do_run, secure_config, password, ro_password, custom_names)


def make_config_from_input(inp: UserInstallInput) -> RunConfig:
    """Makes run config from user input"""
    token = generate_token() if inp.secure_config else ''
    return RunConfig(inp.config_name, '', inp.projector_port,
                     token, inp.password, inp.ro_password, False, inp.custom_names)
