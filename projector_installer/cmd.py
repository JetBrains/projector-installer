# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""Command line interface to projector-installer"""
from os import path
from typing import Any, Optional
import click

from . import global_config
from .global_config import init_config_dir, init_cache_dir

from .actions import do_install_app, do_uninstall_app, do_find_app, do_list_app, do_run_config, \
    do_list_config, do_show_config, do_add_config, do_remove_config, do_edit_config, \
    do_rename_config, do_rebuild_config, do_install_cert, do_update_config
from .license import display_license
from .projector_updates import check_for_projector_updates
from .utils import expand_path


def is_first_start() -> bool:
    """Detects first app start."""
    return not path.isdir(global_config.config_dir)


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option()
@click.option('--config-directory', type=click.Path(),
              default=global_config.config_dir,
              help='Path to configuration directory')
@click.option('--cache-directory', type=click.Path(),
              default='',
              help='Path to download cache directory')
def projector(ctx: Any, config_directory: str, cache_directory: str) -> None:
    """
    This script helps to install, manage, and run JetBrains IDEs with Projector.
    """

    check_for_projector_updates()

    global_config.config_dir = expand_path(config_directory)

    if cache_directory:
        global_config.cache_dir = expand_path(cache_directory)

    if is_first_start():
        display_license()
        init_config_dir()
        print('Please select IDE to install:')
        do_install_app(None, auto_run=True, allow_updates=False, run_browser=True)
    elif not ctx.invoked_subcommand:
        click.echo(ctx.get_help())
    else:
        init_cache_dir()


@click.command(short_help='Find Projector-compatible IDE')
@click.argument('pattern', type=click.STRING, required=False)
def find_app(pattern: Optional[str]) -> None:
    """projector ide find [pattern]

    Find projector-compatible IDE with the name matching to the given pattern.
    If no pattern is specified, finds all the compatible IDEs.
    """
    do_find_app(pattern)


@click.command(short_help='Uninstall selected IDE')
@click.argument('name_pattern', type=click.STRING, required=False)
def uninstall(name_pattern: Optional[str]) -> None:
    """projector ide install [ide_name_pattern]

    Parameter ide_name_pattern is matched to the name of IDE to uninstall.
    If no name pattern is given or the pattern is ambiguous, guides the user through the
    uninstall process.
    """
    do_uninstall_app(name_pattern)


@click.command(short_help='Display installed IDEs')
@click.argument('pattern', type=click.STRING, required=False)
def list_apps(pattern: Optional[str]) -> None:
    """projector ide list [pattern]

    Displays installed IDEs whose names matches to given pattern.
    If no pattern is given, lists all installed IDEs.
    """
    do_list_app(pattern)


@click.command(short_help='List configurations')
@click.argument('pattern', required=False)
def list_config(pattern: Optional[str]) -> None:
    """projector config list [pattern]

    Displays configurations whose names matches to the given pattern.
    If no pattern is given, lists all the configurations.
    """
    do_list_config(pattern)


@click.command(short_help='Show selected configuration details')
@click.argument('config_name', type=click.STRING, required=False)
def show(config_name: Optional[str]) -> None:
    """projector config show [config_name]

    Parameter config_name specifies a desired configuration.
    If not given or ambiguous, selects a configuration interactively.
    """
    do_show_config(config_name)


@click.command(short_help='Add new configuration')
@click.argument('config_name', type=click.STRING, required=False)
@click.argument('ide_path', type=click.STRING, required=False)
@click.option('--expert', default=False, is_flag=True,
              help='Expert mode - set all config parameters')
def add(config_name: Optional[str], ide_path: Optional[str], expert: bool) -> None:
    """projector config add [config_name]

    Add a new configuration.
    """
    do_add_config(config_name, ide_path, not expert)


@click.command(short_help='Remove configuration')
@click.argument('config_name', type=click.STRING, required=False)
def remove(config_name: Optional[str]) -> None:
    """projector config remove [config_name]

    Remove an existing configuration.
    """
    do_remove_config(config_name)


@click.command(short_help='Change existing configuration')
@click.argument('config_name', type=click.STRING, required=False)
def edit(config_name: Optional[str]) -> None:
    """projector config edit [config_name]

    Change an existing configuration.
    """
    do_edit_config(config_name)


@click.command(short_help='Rename existing configuration')
@click.argument('from_name', type=click.STRING, required=True)
@click.argument('to_name', type=click.STRING, required=True)
def rename(from_name: str, to_name: str) -> None:
    """projector config rename from_config_name to_config_name

    Rename an existing configuration.
    """
    do_rename_config(from_name, to_name)


@click.command(short_help='Regenerate all files related to given config')
@click.argument('config_name', type=click.STRING, required=False)
def rebuild(config_name: Optional[str]) -> None:
    """projector config rebuild [config_name]

    Regenerate all files related to given config.
    """
    do_rebuild_config(config_name)


@click.command(short_help='Run selected configuration')
@click.argument('config_name', type=click.STRING, required=False)
@click.option('--run-browser/--no-browser', default=True,
              help='Auto run browser in WSL environment.')
def run(config_name: Optional[str], run_browser: bool) -> None:
    """projector run config_name

    Shortcut for projector config run config_name
    """
    do_run_config(config_name, run_browser)


@click.command(short_help='Update IDE in selected configuration')
@click.argument('config_name', type=click.STRING, required=False)
@click.option('--allow-updates', default=False, is_flag=True,
              help='Allow updates of installed IDE.')
def update(config_name: Optional[str], allow_updates: bool) -> None:
    """projector config update config_name

    Updates IDE in selected config if update is available
    Updates IDE in selected config if update is available
    """
    do_update_config(config_name, allow_updates)


@click.command(short_help='Install and configure selected IDE')
@click.argument('ide_name', type=click.STRING, required=False)
@click.option('--auto-run/--no-auto-run', default=True,
              help='Run installed IDE.')
@click.option('--allow-updates', default=False, is_flag=True,
              help='Allow updates of installed IDE.')
@click.option('--run-browser/--no-browser', default=True,
              help='Auto run browser in WSL environment.')
@click.option('--expert', default=False, is_flag=True,
              help='Expert mode - set all config parameters')
def install_app(ide_name: Optional[str], auto_run: bool,
                allow_updates: bool,
                run_browser: bool, expert: bool) -> None:
    """projector ide install [ide_name]

    Parameter ide_name is the name of IDE to install.
    If no IDE name is given or the pattern is ambiguous, guides the user through the
    install process.
    """
    do_install_app(ide_name, auto_run, allow_updates, run_browser, not expert)


@click.command(short_help='Install user certificate to given config')
@click.argument('config_name', type=click.STRING, required=False)
@click.option('--certificate', type=click.Path(), required=False)
@click.option('--key', type=click.Path(), required=False)
@click.option('--chain', type=click.Path(), required=False)
def install_certificate(config_name: Optional[str], certificate: Optional[str],
                        key: Optional[str], chain: Optional[str]) -> None:
    """projector install-certificate config_name --certificate cert-file
    --key key-file [--chain cert-chain-file]

    Adds user-specified certificate to given config
    """
    do_install_cert(config_name, certificate, key, chain)


@projector.group()
def ide() -> None:
    """
    JetBrains IDE management commands
    """


@projector.group()
def config() -> None:
    """
    Configuration management commands
    """


# IDE commands
ide.add_command(find_app, name='find')
ide.add_command(list_apps, name='list')
ide.add_command(install_app, name='install')
ide.add_command(uninstall, name='uninstall')

# Config commands
config.add_command(list_config, name='list')
config.add_command(show, name='show')
config.add_command(add, name='add')
config.add_command(remove, name='remove')
config.add_command(edit, name='edit')
config.add_command(rename, name='rename')
config.add_command(rebuild, name='rebuild')
config.add_command(run, name='run')
config.add_command(update, name='update')

# Shortcut commands
projector.add_command(find_app, name='find')
projector.add_command(run, name='run')
projector.add_command(install_app, name='install')
projector.add_command(install_certificate, name='install-certificate')
