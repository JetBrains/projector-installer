#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Run config generation stuff"""

import configparser
import io
from os import stat, chmod
from os.path import join
from pathlib import Path
from shlex import quote
from typing import TextIO
from shutil import copy

from .apps import get_launch_script, get_ide_properties_file, IDEA_PROPERTIES_FILE, \
    forbid_updates_for, forbid_plugin_update_notifications
from .global_config import get_projector_server_dir, get_ssl_properties_file
from .run_config import RunConfig, get_run_script_path, CONFIG_INI_NAME
from .secure_config import generate_server_secrets

IDEA_RUN_CLASS = 'com.intellij.idea.Main'
PROJECTOR_RUN_CLASS = 'org.jetbrains.projector.server.ProjectorLauncher'
IDEA_PLATFORM_PREFIX = 'idea.platform.prefix'
TOKEN_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_HANDSHAKE_TOKEN'
RO_TOKEN_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_RO_HANDSHAKE_TOKEN'
SSL_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_SSL_PROPERTIES_PATH'

CLASS_TO_LAUNCH_PROPERTY_NAME = 'org.jetbrains.projector.server.classToLaunch'
HOST_PROPERTY_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_HOST'
PORT_PROPERTY_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_PORT'

MPS_MAIN_CLASS = '${MAIN_CLASS}'


def token_quote(token: str) -> str:
    """Returns shell quoted token"""
    res = quote(token)

    if res:
        if res[0] == res[-1] == '\'':
            return res

        res = f'\"{res}\"'

    return res


def launch_script_last_lines(run_config: RunConfig, main_class: str) -> str:
    """Launch script last lines"""
    line = ' -Djdk.attach.allowAttachSelf=true \\\n'
    line += f' -D{PORT_PROPERTY_NAME}={run_config.projector_port} \\\n'
    line += f' -D{CLASS_TO_LAUNCH_PROPERTY_NAME}={main_class} \\\n'

    if run_config.projector_host != RunConfig.HOST_ALL:
        line += f' -D{HOST_PROPERTY_NAME}={run_config.projector_host} \\\n'

    if run_config.is_secure():
        line += f' -D{SSL_ENV_NAME}=\"{get_ssl_properties_file(run_config.name)}\" \\\n'

    if run_config.is_password_protected():
        line += f' -D{TOKEN_ENV_NAME}={token_quote(run_config.password)} \\\n'
        line += f' -D{RO_TOKEN_ENV_NAME}={token_quote(run_config.ro_password)} \\\n'

    line += f'  {PROJECTOR_RUN_CLASS}\\\n'

    return line


def write_run_script(run_config: RunConfig, src: TextIO, dst: TextIO) -> None:
    """Writes run script from src to dst"""

    for line in src:
        if line.startswith("IDE_BIN_HOME"):
            line = f'IDE_BIN_HOME={quote(join(run_config.path_to_app, "bin"))}\n'
        elif line.find("classpath") != -1:
            line = f' -classpath "$CLASSPATH:$CLASS_PATH:{get_projector_server_dir()}/*" \\\n'
        elif run_config.use_separate_config and line.find('${IDE_PROPERTIES_PROPERTY}') != -1:
            line = f' -Didea.properties.file=' \
                   f'{join(run_config.get_path(), IDEA_PROPERTIES_FILE)} \\\n'
        elif line.find(IDEA_RUN_CLASS) != -1:
            line = launch_script_last_lines(run_config, IDEA_RUN_CLASS)
        elif line.find(MPS_MAIN_CLASS) != -1:
            line = launch_script_last_lines(run_config, MPS_MAIN_CLASS)

        dst.write(line)


def make_run_script(run_config: RunConfig, run_script: str) -> None:
    """Creates run script from ide launch script."""
    idea_script = get_launch_script(run_config.path_to_app)

    with open(idea_script, mode='r', encoding='utf-8') as src, \
            open(run_script, mode='w', encoding='utf-8') as dst:
        write_run_script(run_config, src, dst)

    stats = stat(run_script)
    chmod(run_script, stats.st_mode | 0o0111)


def check_run_script(run_config: RunConfig, run_script_name: str) -> bool:
    """Check if run script corresponds to given config"""
    idea_script = get_launch_script(run_config.path_to_app)
    with open(idea_script, mode='r', encoding='utf-8') as src, \
            open(run_script_name, mode='r', encoding='utf-8') as run_script:
        dst = io.StringIO()
        write_run_script(run_config, src, dst)
        dst.seek(0)
        return dst.read() == run_script.read()


def generate_run_script(run_config: RunConfig) -> None:
    """Generates projector run script"""
    run_script = get_run_script_path(run_config.name)
    make_run_script(run_config, run_script)


def copy_idea_properties_file(run_config: RunConfig) -> None:
    """Copies idea.properties file from install dir to run config"""
    copy(get_ide_properties_file(run_config.path_to_app), run_config.get_path())


IDEA_CONFIG_PATH_PROPERTY = 'idea.config.path'
IDEA_SYSTEM_PATH_PROPERTY = 'idea.system.path'
IDEA_LOG_PATH_PROPERTY = 'idea.log.path'
IDEA_PLUGINS_PATH_PROPERTY = 'idea.plugins.path'


def create_idea_properties_file(run_config: RunConfig) -> None:
    """Copies idea.properties file from install dir to run config
    and set idea.config.path, idea.system.path,
    idea.log.path and idea.plugin.path properties
    """
    copy_idea_properties_file(run_config)
    prop_file_path = join(run_config.get_path(), IDEA_PROPERTIES_FILE)
    with open(prop_file_path, mode='a', encoding='utf-8') as prop_file:
        prop_file.write(f'\n{IDEA_CONFIG_PATH_PROPERTY}={run_config.get_path()}/config')
        prop_file.write(f'\n{IDEA_SYSTEM_PATH_PROPERTY}={run_config.get_path()}/system')
        prop_file.write(f'\n{IDEA_LOG_PATH_PROPERTY}={run_config.get_path()}/log')
        prop_file.write(f'\n{IDEA_PLUGINS_PATH_PROPERTY}={run_config.get_path()}/plugins')


def save_config(run_config: RunConfig) -> None:
    """Saves given run config."""
    config = configparser.ConfigParser(strict=False, interpolation=None)
    config['IDE'] = {}
    config['IDE']['PATH'] = run_config.path_to_app
    config['IDE']['USE_SEPARATE_CONFIG'] = 'True' \
        if run_config.use_separate_config else 'False'  # type: ignore

    config['PROJECTOR'] = {}
    config['PROJECTOR']['PORT'] = str(run_config.projector_port)
    config['PROJECTOR']['HOST'] = run_config.projector_host

    if run_config.is_secure():
        config['SSL'] = {}
        config['SSL']['TOKEN'] = run_config.token

        if run_config.certificate:
            config['SSL']['CERTIFICATE_FILE'] = run_config.certificate
            config['SSL']['KEY_FILE'] = run_config.certificate_key
            config['SSL']['CHAIN_FILE'] = run_config.certificate_chain

    if run_config.is_password_protected():
        config['PASSWORDS'] = {}
        config['PASSWORDS']['PASSWORD'] = run_config.password  # type: ignore
        config['PASSWORDS']['RO_PASSWORD'] = run_config.ro_password  # type: ignore

    if run_config.toolbox:
        config['TOOLBOX'] = {}
        config['TOOLBOX']['TOOLBOX'] = 'True'  # type: ignore

    if run_config.custom_names:
        config['FQDNS'] = {}
        config['FQDNS']['FQDNS'] = run_config.custom_names  # type: ignore

    config['UPDATE'] = {}
    config['UPDATE']['CHANNEL'] = run_config.update_channel

    config_path = run_config.get_path()

    Path(config_path).mkdir(parents=True, exist_ok=True)

    config_path = join(config_path, CONFIG_INI_NAME)

    with open(config_path, mode='w', encoding='utf-8') as configfile:
        config.write(configfile)

    forbid_updates_for(run_config.path_to_app)

    if run_config.use_separate_config:
        create_idea_properties_file(run_config)

    generate_run_script(run_config)

    if run_config.is_secure():
        generate_server_secrets(run_config)

    forbid_plugin_update_notifications(run_config.get_path_to_idea_options_dir())


def check_config(run_config: RunConfig) -> bool:
    """Check if all run config files corresponds to given configuration"""
    run_script = get_run_script_path(run_config.name)
    return check_run_script(run_config, run_script)
