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

"""User dialog related procedures."""

import sys

import click
import netifaces

from .apps import get_installed_apps, get_app_path, get_compatible_app_names
from .run_config import get_run_configs, RunConfig, get_run_config_names, \
    get_used_projector_ports, get_used_http_ports

from .global_config import DEF_HTTP_PORT, DEF_PROJECTOR_PORT


def display_run_configs_names(config_names):
    """Pretty-print config names."""
    for i, config_name in enumerate(config_names):
        print(f'\t{i + 1:4}. {config_name}')


def list_configs(pattern=None):
    """Displays names of run configs, matches to pattern."""
    config_names = get_run_config_names(pattern)
    display_run_configs_names(config_names)


def display_run_configs(run_configs):
    """Display sorted names of given run configs."""
    config_names = list(run_configs.keys())
    config_names.sort()
    display_run_configs_names(config_names)


def find_apps(pattern=None):
    """Pretty-print projector-compatible applications, matched to given pattern."""
    app_names = get_compatible_app_names(pattern)
    for i, app_name in enumerate(app_names):
        print(f'\t{i + 1:4}. {app_name}')


def list_apps(pattern=None):
    """Pretty print the list of installed ide."""
    for i, app in enumerate(get_installed_apps(pattern)):
        print(f'\t{i + 1:4}. {app}')


def select_installed_app(pattern=None):
    """Interactively selects installed ide."""
    apps = get_installed_apps(pattern)

    while True:
        list_apps(pattern)
        prompt = f'Choose an IDE number to uninstall or 0 to exit: [0-{len(apps)}]'
        app_number = click.prompt(prompt, type=int)

        if app_number < 0 or app_number > len(apps):
            print('Invalid number.')
            continue

        if app_number == 0:
            return None

        return apps[app_number - 1]


def select_compatible_app(pattern=None):
    """Interactivelly selects app name from list of projector-compatible applications."""
    app_names = get_compatible_app_names(pattern)

    while True:
        find_apps(pattern)
        prompt = f'Choose IDE number to install or 0 to exit: [0-{len(app_names)}]'
        app_number = click.prompt(prompt, type=int)

        if app_number < 0 or app_number > len(app_names):
            print('Invalid number.')
            continue

        if app_number == 0:
            return None

        return app_names[app_number - 1]


def select_unused_config_name(hint):
    """Generate unused config name."""
    run_configs = get_run_configs()
    cnt = 0
    res = hint

    while res in run_configs:
        cnt += 1
        res = f'{hint}_{cnt}'

    return res


def select_new_config_name(hint):
    """Prompts for new config name and checks for collisions."""
    run_config = get_run_configs()

    if hint:
        hint = select_unused_config_name(hint)
        prompt = 'Enter a new configuration name or press ENTER for default'
    else:
        prompt = 'Enter a new configuration name'

    while True:
        name = click.prompt(prompt, default=hint)

        if not name:
            return None

        if name in run_config:
            print(f'A configuration with name {name} already exists, please choose another name.')
            print('The known configurations:')
            list_configs()
            continue

        return name


def select_run_config(config_name):
    """Interactively select run config."""
    run_configs = get_run_configs(config_name)

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
                return name, run_configs[name]

    return list(run_configs.items())[0]


def select_installed_app_path():
    """Selects installed app and returns path to it."""
    apps = get_installed_apps()

    while True:
        list_apps()
        prompt = f'Choose IDE number to install or 0 to exit: [0-{len(apps)}]'
        app_number = click.prompt(prompt, type=int)

        if app_number < 0 or app_number > len(apps):
            print('Invalid number selected.')
            continue

        if app_number == 0:
            return None

        return get_app_path(apps[app_number - 1])


def select_manual_app_path():
    """Prompts for path to ide."""
    path = click.prompt('Enter the path to IDE', type=str)
    return path


def select_app_path():
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


def get_all_listening_ports():
    """
    Returns all tcp port numbers in LISTEN state (on any address).
    Reads port state from /proc/net/tcp.
    """
    res = []

    with open('/proc/net/tcp', 'r') as file:
        next(file)
        for line in file:
            split_line = line.strip().split(' ')
            hex_port = split_line[1].split(':')[1]
            hex_state = split_line[3]

            if hex_state == '0A':
                res.append(int(hex_port, 16))

    return res


def is_open_port(port):
    """ Checks if tcp port is LISTEN state in system."""
    return port in get_all_listening_ports()


def get_def_port(ports, default):
    """Returns default or first unused in system and in run configs port."""
    port = default

    if len(ports) > 0:
        ports.sort()
        port = ports[-1] + 1

    while is_open_port(port):
        port += 1

    return port


def get_def_http_port():
    """Returns unused port for http server."""
    http_ports = get_used_http_ports()
    return get_def_port(http_ports, DEF_HTTP_PORT)


def get_def_projector_port():
    """Returns unused port for projector server."""
    ports = get_used_projector_ports()
    return get_def_port(ports, DEF_PROJECTOR_PORT)


def get_local_addresses():
    """Returns list of local ip addresses."""
    interfaces = netifaces.interfaces()
    res = []

    for ifs in interfaces:
        addresses = netifaces.ifaddresses(ifs)

        if netifaces.AF_INET in addresses:
            ipv4 = addresses[netifaces.AF_INET]

            for ips in ipv4:
                res.append(ips['addr'])

    return res


def check_listening_address(address):
    """Check entered ip address for validity."""
    if address == 'localhost':
        return True

    return address in get_local_addresses()


def select_http_address(default):
    """Selects address for http listening."""
    while True:
        res = click.prompt('Enter HTTP listening address (press ENTER for default)',
                           default=default)

        if check_listening_address(res):
            return res

        click.echo('You entered incorrect address, please try again.')
        click.echo('You can try to use one of these addresses:')
        local_addresses = ['localhost'] + get_local_addresses()
        for addr in local_addresses:
            click.echo(addr)


def select_http_port():
    """Selects port for http server."""
    port = get_def_http_port()
    return click.prompt('Enter a desired HTTP port (press ENTER for default)', default=port)


def select_projector_port():
    """Selects port for projector server."""
    port = get_def_projector_port()
    return click.prompt('Enter a desired Projector port (press ENTER for default)', default=port)


def edit_config(config: RunConfig):
    """Edits existing config."""
    prompt = 'Enter the path to IDE (press ENTER for default)'
    config.path_to_app = click.prompt(prompt, default=config.path_to_app)

    prompt = 'Enter a HTTP listening address (press ENTER for default)'
    config.http_address = click.prompt(prompt, default=config.http_address)

    prompt = 'Enter a HTTP port (press ENTER for default)'
    config.http_port = click.prompt(prompt, default=config.http_port)

    prompt = 'Enter a Projector port (press ENTER for default)'
    config.projector_port = click.prompt(prompt, default=config.projector_port)

    return config
