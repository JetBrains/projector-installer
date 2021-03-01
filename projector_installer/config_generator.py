#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Run config generation stuff"""

import configparser
import io
from os import mkdir, stat, chmod
from os.path import join, isdir
from typing import TextIO

from .apps import get_launch_script
from .global_config import get_run_configs_dir, get_projector_server_dir, \
    get_ssl_properties_file
from .run_config import RunConfig, get_run_script_path, CONFIG_INI_NAME
from .secure_config import generate_server_secrets

IDEA_RUN_CLASS = 'com.intellij.idea.Main'
PROJECTOR_RUN_CLASS = 'org.jetbrains.projector.server.ProjectorLauncher'
IDEA_PLATFORM_PREFIX = 'idea.platform.prefix'
TOKEN_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_HANDSHAKE_TOKEN'
RO_TOKEN_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_RO_HANDSHAKE_TOKEN'
SSL_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_SSL_PROPERTIES_PATH'

CLASS_TO_LAUNCH_PROPERTY_NAME='org.jetbrains.projector.server.classToLaunch'
HOST_PROPERTY_NAME='org.jetbrains.projector.server.host'
PORT_PROPERTY_NAME='org.jetbrains.projector.server.port'


def write_run_script(run_config: RunConfig, src: TextIO, dst: TextIO) -> None:
    """Writes run script from src to dst"""

    for line in src:
        if line.startswith("IDE_BIN_HOME"):
            line = f'IDE_BIN_HOME={join(run_config.path_to_app, "bin")}\n'
        elif line.find("classpath") != -1:
            line = f' -classpath "$CLASSPATH:{get_projector_server_dir()}/*" \\\n'
        elif line.find(IDEA_RUN_CLASS) != -1:
            line = f' -D{PORT_PROPERTY_NAME}={run_config.projector_port} \\\n'
            line += f' -D{CLASS_TO_LAUNCH_PROPERTY_NAME}={IDEA_RUN_CLASS} \\\n'

            if run_config.projector_host != RunConfig.HOST_ALL:
                line += f' -D{HOST_PROPERTY_NAME}={run_config.projector_host} \\\n'

            if run_config.is_secure():
                line += f' -D{SSL_ENV_NAME}=\"{get_ssl_properties_file(run_config.name)}\" \\\n'

            if run_config.is_password_protected():
                line += f' -D{TOKEN_ENV_NAME}=\"{run_config.password}\" \\\n'
                line += f' -D{RO_TOKEN_ENV_NAME}=\"{run_config.ro_password}\" \\\n'

            line += f'  {PROJECTOR_RUN_CLASS}\\\n'

        dst.write(line)


def make_run_script(run_config: RunConfig, run_script: str) -> None:
    """Creates run script from ide launch script."""
    idea_script = get_launch_script(run_config.path_to_app)

    with open(idea_script, 'r') as src, open(run_script, 'w') as dst:
        write_run_script(run_config, src, dst)

    stats = stat(run_script)
    chmod(run_script, stats.st_mode | 0o0111)


def check_run_script(run_config: RunConfig, run_script_name: str) -> bool:
    """Check if run script corresponds to given config"""
    idea_script = get_launch_script(run_config.path_to_app)
    with open(idea_script, 'r') as src, open(run_script_name, 'r') as run_script:
        dst = io.StringIO()
        write_run_script(run_config, src, dst)
        dst.seek(0)
        return dst.read() == run_script.read()


def generate_run_script(run_config: RunConfig) -> None:
    """Generates projector run script"""
    run_script = get_run_script_path(run_config.name)
    make_run_script(run_config, run_script)


def save_config(run_config: RunConfig) -> None:
    """Saves given run config."""
    config = configparser.ConfigParser()
    config['IDE'] = {}
    config['IDE']['PATH'] = run_config.path_to_app

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

    config_path = join(get_run_configs_dir(), run_config.name)

    if not isdir(config_path):
        mkdir(config_path)

    config_path = join(config_path, CONFIG_INI_NAME)

    with open(config_path, 'w') as configfile:
        config.write(configfile)

    generate_run_script(run_config)

    if run_config.is_secure():
        generate_server_secrets(run_config)


def check_config(run_config: RunConfig) -> bool:
    """Check if all run config files corresponds to given configuration"""
    run_script = get_run_script_path(run_config.name)
    return check_run_script(run_config, run_script)
