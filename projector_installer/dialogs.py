# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""User dialog related procedures."""

import sys
import readline

from os.path import expanduser
from typing import Optional, Dict, List, Tuple, TypeVar, Callable

import click

from .run_config import get_run_configs, RunConfig, get_run_config_names, get_used_projector_ports
from .apps import get_installed_apps, get_app_path, is_toolbox_path, is_valid_app_path
from .secure_config import generate_token
from .utils import get_local_addresses, get_distributive_name
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


def ask(prompt: str, default: bool) -> bool:
    """Returns Yes-No result for given prompt.
    Contains workaround for Linux Mint issue with no-eol-on-default
    """
    question = prompt + (' [Y/n]' if default else ' [y/N]')
    res: bool = click.prompt(question, type=bool, default=default,  # type: ignore
                             show_default=False)

    if res == default and use_eol_workaround():
        print()

    return res


def prompt_with_default(prompt: str, default: str) -> str:
    """Asks for user input with default"""
    res: str = click.prompt(prompt, default=default)

    if res == default and use_eol_workaround():
        print()

    return res


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


NO_EOL_DISTRIBUTIVE_LIST = ['LinuxMint']


def use_eol_workaround() -> bool:
    """Checks if need extra eol"""
    return get_distributive_name() in NO_EOL_DISTRIBUTIVE_LIST


def get_app_list(kind: IDEKind, pattern: Optional[str] = None) -> Tuple[str, List[Product]]:
    """Returns compatible or full app list, depending on user choice"""
    compatible = ask('Do you want to select from Projector-tested IDE only?', default=False)

    if compatible:
        return RunConfig.TESTED, get_compatible_app_names(kind, pattern)

    return RunConfig.NOT_TESTED, get_all_apps(kind, pattern)


def find_apps(pattern: Optional[str] = None) -> None:
    """Pretty-print projector-compatible applications, matched to given pattern."""
    kind = select_ide_kind()

    if kind is None:
        print('No app kind selected, exiting...')
        sys.exit(2)

    channel, apps = get_app_list(kind, pattern)  # pylint: disable=unused-variable
    print_selection_list(list(map(lambda x: x.name, apps)))


def select_app(pattern: Optional[str] = None) -> Tuple[str, Optional[Product]]:
    """Interactively selects app name from list of projector-compatible applications."""
    kind = select_ide_kind()

    if kind is None:
        return RunConfig.UNKNOWN, None

    channel, apps = get_app_list(kind, pattern)

    return channel, select_from_list(apps, lambda it: it.name,
                                     'Choose IDE number to install or 0 to exit')


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
        name: str = prompt_with_default(prompt, default=hint if hint else '')

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
        inst = ask('Do you want to choose an IDE installed by Projector?'
                   ' If NO, at the next step you will have to enter a path '
                   'to a locally installed IDE.', default=True)

        if inst:
            return select_installed_app_path()

        return select_manual_app_path()

    enter = ask('There are no installed Projector IDEs.\nWould you like to specify '
                'a path to IDE manually?', default=True)
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
    res: int = int(prompt_with_default('Enter a desired Projector port (press ENTER for default)',
                                       default=str(port)))
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
    need_password = ask('Would you like to set password for connection?', default=False)

    if need_password:
        password = select_password('Please specify RW password:', default=def_password)

        need_ro_password = ask('Would you like to set separate read-only password?', default=False)

        if need_ro_password:
            ro_password = select_password('Please specify RO password:', default=def_ro_password)
        else:
            ro_password = password

    return password, ro_password


def select_custom_names(default: str = 'localhost') -> str:
    """Asks user for custom domain names"""
    use_custom_names = ask('Would you like to specify custom DNS names '
                           'for Projector access?',
                           default=False)

    custom_names: str = prompt_with_default(
        'Please specify the comma-separated list of custom names',
        default=default) if use_custom_names else ''

    return custom_names


def select_projector_host(default: str = RunConfig.HOST_ALL) -> str:
    """Asks for Projector's listening address(host)"""
    use_host = ask('Would you like to specify listening address (or host) for Projector?',
                   default=False)

    res = prompt_with_default('Enter a Projector listening address (press ENTER for default)',
                              default=default) if use_host else RunConfig.HOST_ALL

    return res


def edit_config(config: RunConfig) -> RunConfig:
    """Edits existing config."""
    config.path_to_app = select_manual_app_path(default=config.path_to_app)
    config.toolbox = False

    if is_toolbox_path(config.path_to_app):
        config.toolbox = ask(
            'The path looks like a path to JetBrains Toolbox-managed app. '
            'Would you like Projector to update the path automatically '
            'when the app updates?', default=True)

    config.projector_port = int(prompt_with_default(
        'Enter a Projector listening port (press ENTER for default)',
        default=str(config.projector_port)))

    config.projector_host = select_projector_host(config.projector_host)
    config.custom_names = select_custom_names(config.custom_names)

    keep_cert = False

    if config.certificate:
        keep_cert = ask('This config uses custom certificate. '
                        'Would you like to keep it?',
                        default=True)

    if not keep_cert:
        config.certificate = ''
        config.certificate_key = ''
        config.certificate_chain = ''
        secure_config = ask(
            'Use secure connection '
            '(this option requires installing a projector\'s certificate to browser)?',
            default=False)

        config.token = generate_token() if secure_config else ''

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
        is_toolbox = ask(
            'The path looks like a path to JetBrains Toolbox-managed app. '
            'Would you like Projector to update the path automatically '
            'when the app updates?', default=True)

    projector_port = get_def_projector_port()
    projector_host = select_projector_host()
    custom_names = select_custom_names()

    password, ro_password = select_password_pair()

    return RunConfig(name=config_name, path_to_app=expanduser(app_path),
                     projector_port=projector_port, projector_host=projector_host,
                     token='', password=password, ro_password=ro_password,
                     toolbox=is_toolbox, custom_names=custom_names)


def get_quick_config(config_name: str) -> RunConfig:
    """Generates user input in quick mode """
    return RunConfig(name=select_unused_config_name(config_name), path_to_app='',
                     projector_port=get_def_projector_port(),
                     projector_host=RunConfig.HOST_ALL,
                     token='', password='', ro_password='',
                     toolbox=False, custom_names='')


def get_user_install_input(config_name_hint: str) -> Optional[RunConfig]:
    """Interactively creates user input"""
    config_name = select_new_config_name(config_name_hint)

    if not config_name:
        return None

    projector_port = get_def_projector_port()
    projector_host = select_projector_host()
    custom_names = select_custom_names()

    password, ro_password = select_password_pair()

    return RunConfig(name=config_name, path_to_app='',
                     projector_port=projector_port, projector_host=projector_host,
                     token='', password=password, ro_password=ro_password,
                     toolbox=False, custom_names=custom_names)
