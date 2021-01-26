#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Secure config related stuff"""
import socket
from os.path import join, isfile
from typing import List, Tuple, Optional, TextIO

import re
import subprocess

from .global_config import get_ssl_dir, get_ssl_properties_file
from .log_utils import init_log, shutdown_log
from .utils import create_dir_if_not_exist, remove_file_if_exist, \
    get_local_addresses, generate_token
from .apps import get_jre_dir
from .run_config import RunConfig, get_path_to_config

PROJECTOR_JKS_NAME = 'projector'
CA_NAME = 'ca'
CA_PASSWORD = '85TibAyPS3NZX3'


def get_projector_jks_file(config_name: str) -> str:
    """Returns full path to projector server key file"""
    return join(get_path_to_config(config_name), f'{PROJECTOR_JKS_NAME}.jks')


def get_projector_csr_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_path_to_config(config_name), f'{PROJECTOR_JKS_NAME}.csr')


def get_projector_crt_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_path_to_config(config_name), f'{PROJECTOR_JKS_NAME}.crt')


def get_ca_crt_file() -> str:
    """Returns full path to ca certificate file"""
    return join(get_ssl_dir(), f'{CA_NAME}.crt')


def get_ca_jks_file() -> str:
    """Returns full path to ca keystore"""
    return join(get_ssl_dir(), f'{CA_NAME}.jks')


def is_ca_exist() -> bool:
    """Checks if ca already generated"""
    ret = isfile(get_ca_jks_file())
    ret = ret and isfile(get_ca_crt_file())
    return ret


def get_ca_dist_name() -> str:
    """Returns CA Dist name"""
    return f'CN=PROJECTOR-{socket.gethostname()}-{generate_token(5)}-CA, ' \
           f'OU=Development, O=Projector, L=SPB, S=SPB, C=RU'


def get_generate_ca_command() -> List[str]:
    """Returns list of args for generate ca"""
    return ['-genkeypair', '-alias', CA_NAME,
            '-dname', get_ca_dist_name(), '-keystore', get_ca_jks_file(),
            '-keypass', CA_PASSWORD, '-storepass', CA_PASSWORD,
            '-keyalg', 'RSA', '-keysize', '4096',
            '-ext', 'KeyUsage:critical=keyCertSign',
            '-ext', 'BasicConstraints:critical=ca:true',
            '-validity', '9999'
            ]


def get_export_ca_command() -> List[str]:
    """Returns list of args for export ca.crt"""
    return ['-export', '-alias', CA_NAME, '-file', get_ca_crt_file(), '-keypass', CA_PASSWORD,
            '-storepass', CA_PASSWORD, '-keystore', get_ca_jks_file(), '-rfc']


DIST_PROJECTOR_NAME = 'CN=Idea, OU=Development, O=Idea, L=SPB, S=SPB, C=RU'


def get_projector_gen_jks_args(run_config: RunConfig) -> List[str]:
    """keytool args for projector jks generation"""
    return [
        '-genkeypair', '-alias', PROJECTOR_JKS_NAME, '-dname', DIST_PROJECTOR_NAME,
        '-keystore', get_projector_jks_file(run_config.name),
        '-keypass', run_config.token, '-storepass', run_config.token,
        '-keyalg', 'RSA', '-keysize', '4096', '-validity', '4500'
    ]


def get_projector_cert_sign_request_args(run_config: RunConfig) -> List[str]:
    """Returns list of args for request cert sign"""
    return [
        '-certreq', '-alias', PROJECTOR_JKS_NAME, '-keypass', run_config.token,
        '-storepass', run_config.token,
        '-keystore', get_projector_jks_file(run_config.name),
        '-file', get_projector_csr_file(run_config.name)
    ]


def is_ip_address(address: str) -> bool:
    """Detects if given string is IP address"""
    return re.match(
        r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.)'
        '{3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$',
        address) is not None


def parse_custom_names(names: str) -> List[str]:
    """Parse comma-separated list of user-provided names"""
    return list(map(lambda s: s.strip(" "), names.split(','))) if names else []


def get_san_alt_names(address: str, custom_names: str) -> Tuple[List[str], List[str]]:
    """Return pair of lists - ip addresses and host names for SAN certificate"""
    ip_addresses = []
    names = set(parse_custom_names(custom_names))

    if address == '0.0.0.0':
        ip_addresses = get_local_addresses()
    else:
        if is_ip_address(address):
            ip_addresses.append(address)
        else:
            names.add(address)

    if '127.0.0.1' in ip_addresses and 'localhost' not in names:
        names.add('localhost')

    host_name = socket.gethostname()
    names.add(host_name)
    names.add(socket.getfqdn(host_name))

    if 'localhost' in names and '127.0.0.1' not in ip_addresses:
        ip_addresses.append('127.0.0.1')

    return ip_addresses, list(names)


def get_projector_san(address: str, custom_names: str) -> str:
    """Returns san"""
    addresses, names = get_san_alt_names(address, custom_names)
    addresses = list(map(lambda s: "IP:" + s, addresses))
    names = list(map(lambda s: "DNS:" + s, names))
    res = addresses + names

    return ",".join(res)


def get_projector_cert_sign_args(run_config: RunConfig) -> List[str]:
    """Returns list of args to sign projector server cert"""
    return [
        '-gencert',
        '-alias', CA_NAME,
        '-storepass', CA_PASSWORD,
        '-keystore', get_ca_jks_file(),
        '-infile', get_projector_csr_file(run_config.name),
        '-outfile', get_projector_crt_file(run_config.name),
        '-ext', 'KeyUsage:critical=digitalSignature,keyEncipherment',
        '-ext', 'EKU=serverAuth',
        '-ext', f'SAN={get_projector_san("0.0.0.0", run_config.custom_names)}',
        '-rfc'
    ]


def get_projector_import_ca_args(run_config: RunConfig) -> List[str]:
    """Returns list of args to import ca to projector jks"""
    return [
        '-import', '-alias', CA_NAME,
        '-file', get_ca_crt_file(),
        '-keystore', get_projector_jks_file(run_config.name),
        '-storetype', 'JKS',
        '-storepass', run_config.token,
        '-noprompt'
    ]


def get_projector_import_cert_args(run_config: RunConfig) -> List[str]:
    """Returns list of args tyo import projector cert to jks"""
    return [
        '-import', '-alias', PROJECTOR_JKS_NAME,
        '-file', get_projector_crt_file(run_config.name),
        '-keystore', get_projector_jks_file(run_config.name),
        '-storetype', 'JKS',
        '-storepass', run_config.token
    ]


def generate_ssl_properties_file(config_name: str, token: str) -> None:
    """Generates ssl.properties file for given config"""
    with open(get_ssl_properties_file(config_name), "w") as file:
        print('STORE_TYPE=JKS', file=file)
        print(f'FILE_PATH={get_projector_jks_file(config_name)}', file=file)
        print(f'STORE_PASSWORD={token}', file=file)
        print(f'KEY_PASSWORD={token}', file=file)


def get_keytool(path_to_app: str) -> str:
    """Returns full path to keytool for given config"""
    return join(get_jre_dir(path_to_app), 'bin', 'keytool')


def remove_server_secrets(config_name: str) -> None:
    """Removes existing server secret files"""
    remove_file_if_exist(get_projector_jks_file(config_name))
    remove_file_if_exist(get_projector_csr_file(config_name))
    remove_file_if_exist(get_projector_crt_file(config_name))
    remove_file_if_exist(get_ssl_properties_file(config_name))


class SecureConfigGenerator:
    """Generate all secret config related stuff for given run config"""

    def __init__(self, run_config: RunConfig):
        self.run_config = run_config
        self.keytool_path = get_keytool(run_config.path_to_app)
        self.log: Optional[TextIO] = None

    def generate_server_secrets(self) -> None:
        """Generate all secret connection related stuff for given config"""
        self.log = init_log(self.run_config.name)
        remove_server_secrets(self.run_config.name)  # remove existing files

        if self.run_config.certificate:
            self._import_user_certificate()
        else:
            if not is_ca_exist():
                self._generate_ca()

            self._generate_projector_jks()

        generate_ssl_properties_file(self.run_config.name, self.run_config.token)

        shutdown_log(0, self.log)

    def _run_subprocess(self, program: str, args: List[str]) -> None:
        """Checked run subprocess"""
        cmd = [program] + args
        subprocess.check_call(cmd, stdout=self.log, stderr=self.log)

    def _run_keytool_with(self, args: List[str]) -> None:
        """Checked run keytool with specified arguments"""
        self._run_subprocess(self.keytool_path, args)

    def _run_openssl_with(self, args: List[str]) -> None:
        """Checked run openssl with specified arguments"""
        self._run_subprocess('openssl', args)

    def _generate_ca(self) -> None:
        """Creates CA"""
        create_dir_if_not_exist(get_ssl_dir())
        self._run_keytool_with(get_generate_ca_command())
        self._run_keytool_with(get_export_ca_command())

    def _generate_projector_jks(self) -> None:
        """Generates projector jks for given config"""
        self._run_keytool_with(get_projector_gen_jks_args(self.run_config))
        self._run_keytool_with(get_projector_cert_sign_request_args(self.run_config))
        self._run_keytool_with(get_projector_cert_sign_args(self.run_config))
        self._run_keytool_with(get_projector_import_ca_args(self.run_config))
        self._run_keytool_with(get_projector_import_cert_args(self.run_config))

    def _import_user_certificate(self) -> None:
        """Imports user-provided certificate"""
        self._export_keychain_to_pkcs12()
        self._import_pkcs12_to_keystore()

    def _get_pkcs12_filename(self) -> str:
        """Full path to temporary keystore"""
        return join(self.run_config.get_path_to_certificate_dir(), f'{PROJECTOR_JKS_NAME}.p12')

    def _export_keychain_to_pkcs12(self) -> None:
        """Export provided cert chain and keyfile to temporary pkcs12 store"""
        args = ['pkcs12', '-export',
                '-in', f'{self.run_config.get_path_to_certificate_file()}',
                '-inkey', f'{self.run_config.get_path_to_key_file()}',
                '-out', f'{self._get_pkcs12_filename()}',
                '-name', f'{PROJECTOR_JKS_NAME}',
                '-password', f'pass:{self.run_config.token}']

        if self.run_config.certificate_chain:
            args = args + ['-certfile', f'{self.run_config.get_path_to_chain_file()}']

        self._run_openssl_with(args)

    def _import_pkcs12_to_keystore(self) -> None:
        """Import temporary pkcs12 keystore to projector jks"""
        args = ['-importkeystore',
                '-destkeystore', f'{get_projector_jks_file(self.run_config.name)}',
                '-srckeystore', f'{self._get_pkcs12_filename()}',
                '-alias', f'{PROJECTOR_JKS_NAME}',
                '-storepass', f'{self.run_config.token}',
                '-srcstorepass', f'{self.run_config.token}']

        self._run_keytool_with(args)


def generate_server_secrets(run_config: RunConfig) -> None:
    """Generate all secret connection related stuff for given config"""
    generator = SecureConfigGenerator(run_config)
    generator.generate_server_secrets()
