#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Secure config related stuff"""
import subprocess
from os.path import join, isfile
import secrets
import string

from .global_config import get_ssl_dir, RunConfig, get_run_configs_dir
from .utils import create_dir_if_not_exist

SSL_PROPERTIES_FILE = 'ssl.properties'
HTTP_CERT_FILE = 'http_server.crt'
HTTP_KEY_FILE = 'http_server.key'
PROJECTOR_JKS_NAME = 'projector'

DEF_TOKEN_LEN = 20
CA_NAME = 'ca'


def generate_token() -> str:
    """Generates token to access server's secrets"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(DEF_TOKEN_LEN))


def get_http_cert_file(config_name: str) -> str:
    """Returns full path to http server certificate file"""
    return join(get_run_configs_dir(), config_name, HTTP_CERT_FILE)


def get_http_key_file(config_name: str) -> str:
    """Returns full path to http server key file"""
    return join(get_run_configs_dir(), config_name, HTTP_KEY_FILE)


def get_ssl_properties_file(config_name: str) -> str:
    """Returns full path to ssl.properties file"""
    return join(get_run_configs_dir(), config_name, SSL_PROPERTIES_FILE)


def get_projector_jks_file(config_name: str) -> str:
    """Returns full path to http server key file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.jks')


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


CA_PASSWORD = '85TibAyPS3NZX3'
DIST_NAME = 'CN=PROJECTOR-CA, OU=Development, O=Projector, L=SPB, S=SPB, C=RU'


def get_generate_ca_command():
    """Returns list of args for generate ca"""
    return ['-genkeypair', '-alias', CA_NAME,
            '-dname', DIST_NAME, '-keystore', get_ca_jks_file(),
            '-keypass', CA_PASSWORD, '-storepass', CA_PASSWORD,
            '-keyalg', 'RSA', '-keysize', '4096',
            '-ext', 'KeyUsage:critical=keyCertSign',
            '-ext', 'BasicConstraints:critical=ca:true',
            '-validity', '9999'
            ]


def get_export_ca_command():
    """Returns list of args for export ca.crt"""
    return ['-export', '-alias', 'ca', '-file', f'{get_ca_cert_file()}', '-keypass', CA_PASSWORD,
            '-storepass', CA_PASSWORD, '-keystore', f'{get_ca_jks_file()}', '-rfc']


def generate_ca(keytool_path: str) -> None:
    """Creates CA"""
    create_dir_if_not_exist(get_ssl_dir())
    cmd = [keytool_path] + get_generate_ca_command()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
    cmd = [keytool_path] + get_export_ca_command()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)


# Create a server certificate
# keytool -genkeypair -v \
#   -alias $ID_VALUE \
#   -dname "CN=$SERVER, OU=Development, O=$SERVER, L=SPB, S=SPB, C=RU" \
#   -keystore $ID_VALUE.jks \
#   -keypass:env PW \
#   -storepass:env PW \
#   -keyalg RSA \
#   -keysize 2048 \
#   -validity 385



def get_projector_gen_jks_args():
    return [
        '-genkeypair', '-alias', PROJECTOR_JKS_NAME, '-dname',
    ]

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
    generate_ssl_properties_file(run_config.name, run_config.token)
    generate_http_cert(run_config)
