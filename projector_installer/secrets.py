#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Secure config related stuff"""
import subprocess
from os import getcwd, chdir
from os.path import join, isfile
import secrets
import string

from .global_config import get_ssl_dir, RunConfig
from .run_config import get_ssl_properties_file, get_projector_jks_file
from .utils import create_dir_if_not_exist

DEF_TOKEN_LEN = 20
CA_NAME = 'ca'


def generate_token() -> str:
    """Generates token to access server's secrets"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(DEF_TOKEN_LEN))


def get_ca_cert_file() -> str:
    """Returns full path to ca certificate file"""
    return join(get_ssl_dir(), f'{CA_NAME}.crt')


def get_ca_key_file() -> str:
    """Returns full path to ca key file"""
    return join(get_ssl_dir(), f'{CA_NAME}.key')


def get_ca_jks_file() -> str:
    """Returns full path to ca keystore"""
    return join(get_ssl_dir(), f'{CA_NAME}.jks')


def is_ca_exist() -> bool:
    """Checks if ca already generated"""
    ret = isfile(get_ca_jks_file())
    ret = ret and isfile(get_ca_cert_file())
    return ret


# keytool -genkeypair -v \
#   -alias ca \
#   -dname "CN=$AUTORITY-CA, OU=Development, O=$AUTORITY, L=SPB, S=SPB, C=RU" \
#   -keystore ca.jks \
#   -keypass:env PW \
#   -storepass:env PW \
#   -keyalg RSA \
#   -keysize 4096 \
#   -ext KeyUsage:critical="keyCertSign" \
#   -ext BasicConstraints:critical="ca:true" \
#   -validity 9999
#

CA_PASSWORD = '85TibAyPS3NZX3'
DIST_NAME = '"CN=PROJECTOR-CA, OU=Development, O=Projector, L=SPB, S=SPB, C=RU"'

GENERATE_CA = ['-genkeypair', '-alias', CA_NAME,
               '-dbname', DIST_NAME, '-keystore', get_ca_jks_file(),
               '-keypass', CA_PASSWORD, '-storepass', CA_PASSWORD,
               '-keyalg', 'RSA', '-keysize', '4096',
               '-ext', 'KeyUsage:critical="keyCertSign"',
               '-ext', 'BasicConstraints:critical="ca:true"',
               '-validity', '9999'
               ]

#
# keytool -export -v \
#   -alias ca \
#   -file ca.crt \
#   -keypass:env PW \
#   -storepass:env PW \
#   -keystore ca.jks \
#   -rfc


EXPORT_CA = ['-export', '-alias', 'ca', '-file', f'{get_ca_cert_file()}', '-keypass', CA_PASSWORD,
             '-storepass', CA_PASSWORD, '-keystore', f'{get_ca_jks_file()}', '-rfc']


def generate_ca(keytool_path: str) -> None:
    """Creates CA"""
    cwd = getcwd()
    create_dir_if_not_exist(get_ssl_dir())
    chdir(get_ssl_dir())
    # generate ca
    cmd = [keytool_path] + GENERATE_CA
    subprocess.check_call(cmd)
    cmd = [keytool_path] + EXPORT_CA
    subprocess.check_call(cmd)

    chdir(cwd)


def generate_projector_jks(run_config: RunConfig, keytool_path: str) -> None:
    """Generates projector jks for given config"""
    file_name = get_projector_jks_file(run_config.name)


def generate_ssl_properties_file(config_name: str, token: str) -> None:
    """Generates ssl.properties file for given config"""
    with open(get_ssl_properties_file(config_name), "w") as file:
        print('STORE_TYPE=JKS', file=file)
        print(f'FILE_PATH={get_projector_jks_file(config_name)}', file=file)
        print(f'STORE_PASSWORD={token}', file=file)
        print(f'KEY_PASSWORD={token}', file=file)


def get_jbr_keytool(path_to_app: str) -> str:
    """Returns full path to keytool for given config"""
    return join(path_to_app, 'jbr', 'bin', 'keytool')


def generate_http_cert(run_config: RunConfig) -> None:
    """Generates http certificate and key files"""


def generate_server_secrets(run_config: RunConfig) -> None:
    """Generate all secret connection related stuff for given config"""
    keytool_path = get_jbr_keytool(run_config.path_to_app)
    if not is_ca_exist():
        generate_ca(keytool_path)

    generate_projector_jks(run_config, keytool_path)
