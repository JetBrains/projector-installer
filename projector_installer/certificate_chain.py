#  Copyright 2000-2021 JetBrains s.r.o.
#  Use of this source code is governed by the Apache 2.0 license that can be found
#  in the LICENSE file.

"""Functions related to obtaining certificate chain file"""
from tempfile import NamedTemporaryFile
from typing import Tuple
from urllib.request import urlopen

from OpenSSL import crypto  # type: ignore
from OpenSSL.crypto import _lib, _ffi, X509  # type: ignore
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import oid, load_der_x509_certificate, load_pem_x509_certificate
from cryptography.x509.extensions import ExtensionNotFound  # type: ignore
from cryptography.x509.extensions import AuthorityInformationAccess  # type: ignore
from cryptography.x509.oid import ExtensionOID  # type: ignore


def convert_der_to_pem(der_data: bytes) -> bytes:
    """Convert certificate from DER to PEM format"""
    cert = load_der_x509_certificate(der_data, default_backend())
    return cert.public_bytes(serialization.Encoding.PEM)


def get_aia_location_from_cert(cert_data: bytes) -> str:
    """Extract AIA location CA_ISSUERS URL from certificate if exist"""
    cert = load_pem_x509_certificate(cert_data, default_backend())

    if cert.issuer == cert.subject:  # root (or self-signed) certificate
        return ''

    try:
        ext = cert.extensions.get_extension_for_oid(ExtensionOID.AUTHORITY_INFORMATION_ACCESS)
    except ExtensionNotFound:
        return ''

    asa: AuthorityInformationAccess = ext.value

    for loc in asa:
        if loc.access_method == oid.AuthorityInformationAccessOID.CA_ISSUERS:
            return str(loc.access_location.value)

    return ''


def is_pkcs7_data(content_type: str) -> bool:
    """Detects pkcs7 container by content type header value"""
    return content_type == 'application/pkcs7-mime'


def download_certificate(url: str) -> Tuple[bool, bytes]:
    """Downloads certificate"""
    with urlopen(url) as resp:
        code = resp.getcode()

        if code != 200:
            raise IOError(f'HTTP error code: {code}')

        return is_pkcs7_data(resp.headers['Content-Type']), bytes(resp.read())


# pylint: disable=protected-access
def get_pem_data_from_pkcs7(data: bytes) -> bytes:
    """Extracts certificate from pkcs7 data and convert it to PEM data"""
    pkcs7 = crypto.load_pkcs7_data(crypto.FILETYPE_ASN1, data)
    certs = _ffi.NULL

    if pkcs7.type_is_signed():
        certs = pkcs7._pkcs7.d.sign.cert
    elif pkcs7.type_is_signedAndEnveloped():
        certs = pkcs7._pkcs7.d.signed_and_enveloped.cert

    if _lib.sk_X509_num(certs) > 1:
        raise Exception('Too many certificates')

    pycert = X509.__new__(X509)
    pycert._x509 = _lib.X509_dup(_lib.sk_X509_value(certs, 0))

    return bytes(crypto.dump_certificate(crypto.FILETYPE_PEM, pycert))


def get_certificate_chain(path_to_certificate: str) -> str:
    """Retrieves and stores certificate chain for given certificate if possible"""
    with open(path_to_certificate, 'rb') as file:
        next_cert_url = get_aia_location_from_cert(file.read())
        chain_data: bytes = bytes()

        while next_cert_url:
            is_pkcs7, data = download_certificate(next_cert_url)

            if is_pkcs7:
                pem_data = get_pem_data_from_pkcs7(data)
            else:
                pem_data = convert_der_to_pem(data)

            chain_data += pem_data

            next_cert_url = get_aia_location_from_cert(pem_data)

    if chain_data:
        with NamedTemporaryFile(suffix='.pem', delete=False, mode='wb') as res:
            res.write(chain_data)
            return res.name

    return ''
