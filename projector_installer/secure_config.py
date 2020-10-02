#  Copyright 2000-2020 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Secure config related stuff"""
import socket
from os.path import join, isfile
from typing import List, Tuple

import re
import subprocess
import secrets
import string

from .global_config import get_ssl_dir, RunConfig, get_run_configs_dir
from .utils import create_dir_if_not_exist, remove_file_if_exist, get_local_addresses

SSL_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_SSL_PROPERTIES_PATH'
TOKEN_ENV_NAME = 'ORG_JETBRAINS_PROJECTOR_SERVER_HANDSHAKE_TOKEN'

SSL_PROPERTIES_FILE = 'ssl.properties'
PROJECTOR_JKS_NAME = 'projector'
HTTP_SERVER = 'http_server'

DEF_TOKEN_LEN = 20
CA_NAME = 'ca'
CA_PASSWORD = '85TibAyPS3NZX3'


def generate_token(length: int = DEF_TOKEN_LEN) -> str:
    """Generates token to access server's secrets"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))


def get_http_crt_file(config_name: str) -> str:
    """Returns full path to http server certificate file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.crt')


def get_http_key_file(config_name: str) -> str:
    """Returns full path to http server key file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.key')


def get_http_csr_file(config_name: str) -> str:
    """Returns full path to projector server csr file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.csr')


def get_http_jks_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_run_configs_dir(), config_name, f'{HTTP_SERVER}.jks')


def get_ssl_properties_file(config_name: str) -> str:
    """Returns full path to ssl.properties file"""
    return join(get_run_configs_dir(), config_name, SSL_PROPERTIES_FILE)


def get_projector_jks_file(config_name: str) -> str:
    """Returns full path to projector server key file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.jks')


def get_projector_pkcs12_file(config_name: str) -> str:
    """Returns full path to projector server key file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.p12')


def get_projector_csr_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.csr')


def get_projector_crt_file(config_name: str) -> str:
    """Returns full path to projector server crt file"""
    return join(get_run_configs_dir(), config_name, f'{PROJECTOR_JKS_NAME}.crt')


def get_ca_crt_file() -> str:
    """Returns full path to ca certificate file"""
    return join(get_ssl_dir(), f'{CA_NAME}.crt')


def get_ca_key_file() -> str:
    """Returns full path to ca key file"""
    return join(get_ssl_dir(), f'{CA_NAME}.key')


def get_ca_jks_file() -> str:
    """Returns full path to ca keystore"""
    return join(get_ssl_dir(), f'{CA_NAME}.jks')


def get_ca_pkcs12_file() -> str:
    """Returns full path to ca keystore"""
    return join(get_ssl_dir(), f'{CA_NAME}.p12')


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


def get_convert_ca_to_pkcs12() -> List[str]:
    """Returns list of args for convert ca to pkcs12 format"""
    return [
        '-importkeystore', '-srckeystore', get_ca_jks_file(),
        '-srcstoretype', 'JKS',
        '-srcstorepass', CA_PASSWORD,
        '-destkeystore', get_ca_pkcs12_file(),
        '-deststoretype', 'pkcs12',
        '-deststorepass', CA_PASSWORD
    ]


def get_extract_ca_key_args() -> List[str]:
    """Returns list of openssl args for extract ca key"""
    return [
        'pkcs12',
        '-in', get_ca_pkcs12_file(),
        '-nodes',
        '-nocerts',
        '-out', get_ca_key_file(),
        '-passin', f'pass:{CA_PASSWORD}'
    ]


def generate_ca(keytool_path: str) -> None:
    """Creates CA"""
    create_dir_if_not_exist(get_ssl_dir())

    cmd = [keytool_path] + get_generate_ca_command()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [keytool_path] + get_export_ca_command()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [keytool_path] + get_convert_ca_to_pkcs12()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = ['openssl'] + get_extract_ca_key_args()
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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


def get_san_alt_names(address: str) -> Tuple[List[str], List[str]]:
    """Return pair of lists - ip addresses and host names for SAN certificate"""
    ip_addresses = []
    names = []

    if address == '0.0.0.0':
        ip_addresses = get_local_addresses()
    else:
        if is_ip_address(address):
            ip_addresses.append(address)
        else:
            names.append(address)

    if '127.0.0.1' in ip_addresses and 'localhost' not in names:
        names.append('localhost')

    if 'localhost' in names and '127.0.0.1' not in ip_addresses:
        ip_addresses.append('127.0.0.1')

    return ip_addresses, names


def get_projector_san(address: str) -> str:
    """Returns san"""
    addresses, names = get_san_alt_names(address)
    addresses = list(map(lambda s: "IP:" + s, addresses))
    names = list(map(lambda s: "DNS:" + s, names))
    res = addresses + names

    return ",".join(res)


def get_projector_cert_sign_args(run_config: RunConfig) -> List[str]:
    """Returns list of args to sign projector server cert"""
    return [
        '-gencert',
        '-alias', CA_NAME,
        '-keypass', run_config.token,
        '-storepass', CA_PASSWORD,
        '-keystore', get_ca_jks_file(),
        '-infile', get_projector_csr_file(run_config.name),
        '-outfile', get_projector_crt_file(run_config.name),
        '-ext', 'KeyUsage:critical=digitalSignature,keyEncipherment',
        '-ext', 'EKU=serverAuth',
        '-ext', f'SAN={get_projector_san(run_config.http_address)}',
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


def generate_projector_jks(run_config: RunConfig) -> None:
    """Generates projector jks for given config"""

    keytool_path = get_jbr_keytool(run_config.path_to_app)

    cmd = [keytool_path] + get_projector_gen_jks_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_cert_sign_request_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_cert_sign_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_import_ca_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cmd = [keytool_path] + get_projector_import_cert_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


DIST_HTTP_NAME = 'CN=Http, OU=Development, O=Idea, L=SPB, S=SPB, C=RU'


def get_http_gen_args(run_config: RunConfig) -> List[str]:
    """keytool args for http keypair generation"""
    return [
        '-genkeypair', '-alias', HTTP_SERVER, '-dname', DIST_HTTP_NAME,
        '-keystore', get_http_jks_file(run_config.name),
        '-keypass', run_config.token, '-storepass', run_config.token,
        '-keyalg', 'RSA', '-keysize', '4096', '-validity', '4500'
    ]


OPENSSL_REQ_CNF = 'server-san-req.cnf'


def get_openssl_req_cnf_file(config_name: str) -> str:
    """Returns full path to openssl config file for SAN req"""
    return join(get_run_configs_dir(), config_name, f'{OPENSSL_REQ_CNF}')


REQ_CNF_CONTENT = """
[ req ]
v3_extensions = v3_req
distinguished_name = req_distinguished_name
prompt = no

[ req_distinguished_name ]
countryName                 = RU
countryName_default         = RU
stateOrProvinceName         = SPB
stateOrProvinceName_default = SPB
localityName                = SPB
localityName_default        = SPB
organizationName            = Projector
organizationName_default    = Projector
commonName                  = localhost
commonName_default          = localhost
commonName_max              = 64


[ v3_req ]
subjectAltName =  @alt_names

[ alt_names ]
"""


def generate_req_cnf(config_name: str, addresses: List[str], names: List[str]) -> None:
    """Generate OpenSSL config for sign request"""
    res = REQ_CNF_CONTENT

    for i, address in enumerate(addresses):
        res += f'IP.{i + 1} = {address}\n'

    for i, name in enumerate(names):
        res += f'DNS.{i + 1} = {name}\n'

    with open(get_openssl_req_cnf_file(config_name), 'w') as file:
        file.write(res)


OPENSSL_SIGN_CNF = 'server-san-sign.cnf'


def get_openssl_sign_cnf_file(config_name: str) -> str:
    """Returns full path to openssl config file for SAN sign cert"""
    return join(get_run_configs_dir(), config_name, f'{OPENSSL_SIGN_CNF}')


SIGN_CNF_CONTENT = """
[ v3_sign ]
subjectAltName = @alt_names

[ alt_names ]
"""


def generate_sign_cnf(config_name: str, addresses: List[str], names: List[str]) -> None:
    """Generate OpenSSL config for signing certificate"""
    res = SIGN_CNF_CONTENT

    for i, address in enumerate(addresses):
        res += f'IP.{i + 1} = {address}\n'

    for i, name in enumerate(names):
        res += f'DNS.{i + 1} = {name}\n'

    with open(get_openssl_sign_cnf_file(config_name), 'w') as file:
        file.write(res)


def get_openssl_generate_key_args(run_config: RunConfig) -> List[str]:
    """Get openssl generate keys arg"""
    return ['genrsa',
            '-out', get_http_key_file(run_config.name),
            '2048'
            ]


DN = "/C=RU/ST=SPB/L=SPB/O=Projector/OU=projector-installer/CN=localhost"


def get_openssl_generate_cert_req(run_config: RunConfig) -> List[str]:
    """Returns openssl args to generate cert sign request"""
    return ['req', '-new',
            '-key', get_http_key_file(run_config.name),
            '-out', get_http_csr_file(run_config.name),
            '-config', get_openssl_req_cnf_file(run_config.name),
            '-subj', DN
            ]


def get_openssl_sign_args(run_config: RunConfig) -> List[str]:
    """Returns openssl list of args for sign cert"""
    return [
        'x509', '-req',
        '-in', get_http_csr_file(run_config.name),
        '-out', get_http_crt_file(run_config.name),
        '-extfile', get_openssl_sign_cnf_file(run_config.name),
        '-extensions', 'v3_sign',
        '-CA', get_ca_crt_file(),
        '-CAkey', get_ca_key_file(),
        '-CAcreateserial',
        '-days', '4500'
    ]


def generate_http_cert(run_config: RunConfig) -> None:
    """Generates http certificate and key files"""
    cmd = ['openssl'] + get_openssl_generate_key_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    (ip_addresses, names) = get_san_alt_names(run_config.http_address)

    generate_req_cnf(run_config.name, ip_addresses, names)
    cmd = ['openssl'] + get_openssl_generate_cert_req(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    generate_sign_cnf(run_config.name, ip_addresses, names)
    cmd = ['openssl'] + get_openssl_sign_args(run_config)
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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


def are_exist_server_secrets(config_name: str) -> bool:
    """Returns True if all secure connection related server config files exist"""
    ret: bool = isfile(get_projector_jks_file(config_name))
    ret = ret and isfile(get_projector_csr_file(config_name))
    ret = ret and isfile(get_projector_crt_file(config_name))
    ret = ret and isfile(get_ssl_properties_file(config_name))
    ret = ret and isfile(get_http_csr_file(config_name))
    ret = ret and isfile(get_http_crt_file(config_name))
    ret = ret and isfile(get_http_key_file(config_name))

    return ret


def remove_server_secrets(config_name: str) -> None:
    """Removes existing server secret files"""
    remove_file_if_exist(get_projector_jks_file(config_name))
    remove_file_if_exist(get_projector_csr_file(config_name))
    remove_file_if_exist(get_projector_crt_file(config_name))
    remove_file_if_exist(get_ssl_properties_file(config_name))
    remove_file_if_exist(get_http_csr_file(config_name))
    remove_file_if_exist(get_http_crt_file(config_name))
    remove_file_if_exist(get_http_key_file(config_name))


def generate_server_secrets(run_config: RunConfig) -> None:
    """Generate all secret connection related stuff for given config"""
    keytool_path = get_jbr_keytool(run_config.path_to_app)
    if not is_ca_exist():
        generate_ca(keytool_path)

    if not are_exist_server_secrets(run_config.name):  # if not all files exist
        remove_server_secrets(run_config.name)  # remove existing files
        generate_projector_jks(run_config)
        generate_ssl_properties_file(run_config.name, run_config.token)
        generate_http_cert(run_config)


def is_secure(run_config: RunConfig) -> bool:
    """Checks if secure configuration"""
    return run_config.token != ''
