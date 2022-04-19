# Copyright 2000-2022 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""User dialog related procedures."""
import platform
import sys
import readline
from enum import Enum, auto
from getpass import getpass

from os.path import expanduser
from typing import Optional, Dict, List, Tuple, TypeVar, Callable

import click
from click import INT

from .defaults import get_defaults, Defaults
from .run_config import get_run_configs, RunConfig, get_run_config_names, get_used_projector_ports
from .apps import get_installed_apps, get_app_path, is_toolbox_path, is_valid_app_path, \
    get_toolbox_managed_apps, get_path_to_toolbox_app, is_toolbox_installed
from .secure_config import generate_token
from .utils import get_local_addresses, generate_random_password
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


def get_user_input(prompt: str, default: str) -> str:
    """Get user input string"""
    res = input(prompt)

    if not res:
        res = default

    return res


YES_NO_STR = ['y', 'Y', 'n', 'N']


def is_boolean_input(inp: str) -> bool:
    """Checks if is valid boolean input"""
    return inp in YES_NO_STR


def ask(prompt: str, default: bool) -> bool:
    """Returns Yes-No result for given prompt.
    Contains workaround for Linux Mint issue with no-eol-on-default
    """
    question = prompt + (' [Y/n]' if default else ' [y/N]')
    def_str = 'y' if default else 'n'
    res = get_user_input(question, def_str)

    while not is_boolean_input(res):
        print("Invalid input, please answer y or n.")
        res = get_user_input(question, def_str)

    return res in ('y', 'Y')


def prompt_with_default(prompt: str, default: str) -> str:
    """Get string user input with def prompt"""
    prompt = prompt + f' [{default}]: '
    return get_user_input(prompt, default)


T = TypeVar('T', IDEKind, Product, str)  # pylint: disable=C0103


def select_from_list(data: List[T], name: Callable[[T], str], prompt: str) -> Optional[T]:
    """Interactively selects named entity from given list"""
    names: List[str] = list(map(name, data))
    prompt = f'{prompt}: [0-{len(names)}]'

    while True:
        print_selection_list(names)
        pos: int = click.prompt(prompt, type=INT)

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


def select_ide_kind(pattern: Optional[str]) -> Optional[IDEKind]:
    """Select an IDE kind that matches the given pattern or interactively select one otherwise"""
    kinds = [k for k in IDEKind if k != IDEKind.Unknown]
    if pattern:
        pattern = pattern.lower().split(' ')[0]
        matched_kinds = [k for k in kinds if k.name.lower().startswith(pattern)]
        if len(matched_kinds) == 1:
            return matched_kinds[0]
        if len(matched_kinds) > 1:
            kinds = matched_kinds
    return select_from_list(kinds, lambda it: it.name, 'Choose IDE type or 0 to exit')


def get_app_list(kind: IDEKind, pattern: Optional[str] = None) -> Tuple[str, List[Product]]:
    """Returns compatible or full app list, depending on user choice"""
    compatible = ask('Do you want to select from Projector-tested IDE only?', default=False)

    if compatible:
        return RunConfig.TESTED, get_compatible_app_names(kind, pattern)

    return RunConfig.NOT_TESTED, get_all_apps(kind, pattern)


def find_apps(pattern: Optional[str] = None) -> None:
    """Pretty-print projector-compatible applications, matched to given pattern."""
    kind = select_ide_kind(pattern)

    if kind is None:
        print('No app kind selected, exiting...')
        sys.exit(2)

    channel, apps = get_app_list(kind, pattern)  # pylint: disable=unused-variable
    print_selection_list(list(map(lambda x: x.name, apps)))


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
            config_number = click.prompt(prompt, type=INT)

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
        prompt = f'Enter the path to IDE (<enter> for {default}, <tab> for complete): '
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

        click.echo(f'Path {path} does not look like a valid path.')


def select_app(pattern: Optional[str] = None) -> Tuple[str, Optional[Product]]:
    """Selects app name from list of projector-compatible applications."""
    kind = select_ide_kind(pattern)

    if kind is None:
        return RunConfig.UNKNOWN, None

    if pattern:
        matched_apps = get_all_apps(kind, pattern)
        if len(matched_apps) == 1:
            return RunConfig.NOT_TESTED, matched_apps[0]

    channel, apps = get_app_list(kind)

    return channel, select_from_list(apps, lambda it: it.name,
                                     'Choose IDE number to install or 0 to exit')


# pylint: disable=C0103
class AppSource(Enum):
    """Application source"""
    Unknown = auto()
    ProjectorInstalled = auto()
    UserInstalled = auto()
    ToolboxManaged = auto()


def select_app_source() -> AppSource:
    """Select application source"""
    names: List[str] = ["User-installed (local path)"]
    sources: List[AppSource] = [AppSource.UserInstalled]

    apps = get_installed_apps()

    if apps:
        names.append("Projector-installed")
        sources.append(AppSource.ProjectorInstalled)

    # if is_toolbox_installed():
    names.append("Toolbox-managed (with updates integration)")
    sources.append(AppSource.ToolboxManaged)

    if len(sources) == 1:
        return sources[0]

    prompt = f'Select application source or 0 to exit [0-{len(names)}]'

    while True:
        print_selection_list(names)
        pos: int = click.prompt(prompt, type=INT)

        if pos < 0 or pos > len(names):
            print('Invalid number.')
            continue

        if pos == 0:
            return AppSource.Unknown

        return sources[pos - 1]


def select_toolbox_managed_app() -> Optional[str]:
    """Return path to toolbox-managed app"""
    apps = get_toolbox_managed_apps()

    if not is_toolbox_installed():
        click.secho("Looks like you didn't installed the Toolbox app yet.",
                    bold=True, fg='yellow')
        click.secho("Give it a try: https://www.jetbrains.com/toolbox-app/",
                    bold=True, fg='yellow')
        return None

    res = select_from_list(apps, lambda it: it, 'Choose IDE number to install or 0 to exit')
    return res if res is None else get_path_to_toolbox_app(res)


def select_app_path() -> Tuple[bool, Optional[str]]:
    """Select path to ide."""
    app_source = select_app_source()

    if app_source == AppSource.ProjectorInstalled:
        app_path = select_installed_app_path()
        is_toolbox = False
    elif app_source == AppSource.UserInstalled:
        app_path = select_manual_app_path()
        is_toolbox = False

        if is_toolbox_path(app_path):
            is_toolbox = ask(
                'The path looks like a path to JetBrains Toolbox-managed app. '
                'Would you like Projector to update the path automatically '
                'when the app updates?', default=True)
    elif app_source == AppSource.ToolboxManaged:
        app_path = select_toolbox_managed_app()
        is_toolbox = True
    else:  # to make lint happy
        is_toolbox = False
        app_path = None

    return is_toolbox, app_path


def get_all_listening_ports() -> List[int]:
    """
    Returns all tcp port numbers in LISTEN state (on any address).
    Reads port state from /proc/net/tcp.
    """
    res: List[int] = []

    if platform.system() != 'Linux':
        return res

    with open('/proc/net/tcp', mode='r', encoding='utf-8') as file:
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


def enter_password(prompt: str, default: str = '') -> str:
    """Hidden password input"""
    try:
        password = getpass(prompt)
    except (KeyboardInterrupt, EOFError):
        click.echo(None)
        sys.exit(1)

    if not password and default:
        password = default

    return password


def select_password(prompt: str, default: str = '') -> str:
    """Prompts for password"""
    matched_passwords = False
    password: str = ''

    while not matched_passwords:
        password = enter_password(prompt, default)

        if default and password == default:
            return password

        repeat = enter_password("Repeat password:", default)

        matched_passwords = password == repeat

        if not matched_passwords:
            click.echo('Password mismatch. Please try again.')

    return password


def select_password_pair(def_password: str = '', def_ro_password: str = '') -> Tuple[str, str]:
    """Prompts for the pair of access passwords if needed"""
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


def select_host_names(default: str = '') -> str:
    """Asks user for custom domain names"""
    use_custom_names = ask('Would you like to specify hostname '
                           'for Projector access?',
                           default=False)

    host_names: str = prompt_with_default(
        'Please specify the comma-separated list of host names',
        default=get_defaults().get_host(default)) if use_custom_names else ''

    return host_names


def select_projector_listening_address(default: str = RunConfig.HOST_LOCALHOST) -> str:
    """Asks for Projector's listening address(host)"""
    use_host = ask('Would you like to specify listening address (or host) for Projector?',
                   default=False)

    res = prompt_with_default('Enter a Projector listening address (press ENTER for default)',
                              default=default) if use_host else RunConfig.HOST_LOCALHOST

    return res


def select_update_channel(default: str) -> str:
    """Select update channel"""
    channels = [RunConfig.TESTED, RunConfig.NOT_TESTED]
    res = select_from_list(channels, lambda it: it,
                           f'Choose update channel or 0 to keep current({default})')
    return default if res is None else res


def edit_config(config: RunConfig) -> RunConfig:
    """Edits existing config."""
    config.path_to_app = select_manual_app_path(default=config.path_to_app)
    config.use_separate_config = ask('Use separate configuration directory for this config?',
                                     default=config.use_separate_config)
    config.toolbox = False

    if is_toolbox_path(config.path_to_app):
        config.toolbox = ask(
            'The path looks like a path to JetBrains Toolbox-managed app. '
            'Would you like Projector to update the path automatically '
            'when the app updates?', default=True)

    config.projector_port = int(prompt_with_default(
        'Enter a Projector listening port (press ENTER for default)',
        default=str(config.projector_port)))

    config.projector_host = select_projector_listening_address(config.projector_host)
    config.custom_names = select_host_names(config.custom_names)

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

    if not config.toolbox:
        config.update_channel = select_update_channel(config.update_channel)

    return config


def make_run_config(config_name: str, app_path: Optional[str] = None) -> RunConfig:
    """Creates run config with specified app_path."""

    if app_path is None:
        is_toolbox, app_path = select_app_path()
    else:
        is_toolbox = is_toolbox_path(app_path)

    if not app_path:
        print('IDE was not selected, exiting...')
        sys.exit(1)

    separate_config = ask('Use separate configuration directory for this config?',
                          default=False)

    projector_port = get_def_projector_port()
    projector_host = select_projector_listening_address()
    custom_names = select_host_names()

    password, ro_password = select_password_pair()

    return RunConfig(name=config_name, path_to_app=expanduser(app_path),
                     use_separate_config=separate_config,
                     projector_port=projector_port, projector_host=projector_host,
                     token='', password=password, ro_password=ro_password,
                     toolbox=is_toolbox, custom_names=custom_names)


def get_quick_config(config_name: str) -> RunConfig:
    """Generates user input in quick mode """
    return RunConfig(name=select_unused_config_name(config_name), path_to_app='',
                     use_separate_config=False,
                     projector_port=get_def_projector_port(),
                     projector_host=RunConfig.HOST_LOCALHOST,
                     token='',
                     password=generate_random_password(),
                     ro_password=generate_random_password(),
                     toolbox=False, custom_names=get_defaults().host)


def get_user_install_input(config_name_hint: str) -> Optional[RunConfig]:
    """Interactively creates user input"""
    config_name = select_new_config_name(config_name_hint)

    if not config_name:
        return None

    separate_config = ask('Use separate configuration directory for this config?',
                          default=False)

    projector_port = get_def_projector_port()
    projector_host = select_projector_listening_address()
    custom_names = select_host_names()

    password, ro_password = select_password_pair()

    return RunConfig(name=config_name, path_to_app='',
                     use_separate_config=separate_config,
                     projector_port=projector_port, projector_host=projector_host,
                     token='', password=password, ro_password=ro_password,
                     toolbox=False, custom_names=custom_names)


def get_user_defaults(hostname: Optional[str]) -> Defaults:
    """Returns Defaults"""
    defaults = get_defaults()

    if hostname:
        defaults.host = hostname
    else:
        use_default_host = ask('Would you like to specify default hostname '
                               'for Projector access?',
                               default=True)

        defaults.host = prompt_with_default(
            'Please specify default hostname for Projector '
            '(you can specify several names, separated by comma): ',
            default=get_defaults().get_host()) if use_default_host else ''

    return defaults
