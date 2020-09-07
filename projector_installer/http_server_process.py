# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""HTTP server process module."""

from os import chdir
from typing import Any, Optional
from http.server import SimpleHTTPRequestHandler
from multiprocessing import Process

import socketserver
import socket
import ssl

from .global_config import RunConfig
from .secure_config import get_http_crt_file, get_http_key_file, is_secure


class NoLogServer(SimpleHTTPRequestHandler):
    """Custom http server class to serve static projector client files."""
    address: str = ''
    port: str = ''
    projector_port: str = ''
    token: str = ''

    def log_message(self, *args: Any) -> None:
        pass

    def do_GET(self) -> None:
        try:
            if self.need_redirect():
                self.send_response(301)
                self.send_header('Location', NoLogServer.redirect_url())
                self.end_headers()
            else:
                super().do_GET()
        except socket.error:
            pass

    @classmethod
    def init_with(cls, run_config: RunConfig) -> None:
        """Initializes server with run config params"""
        cls.address = run_config.http_address
        cls.port = str(run_config.http_port)
        cls.projector_port = str(run_config.projector_port)
        cls.token = run_config.token

    @classmethod
    def redirect_url(cls) -> str:
        """Constructs redirect url."""

        if len(cls.token) > 0:  # secure connection
            return f'https://{cls.address}:{cls.port}/index.html?' \
                   f'host={cls.address}&port={cls.projector_port}'

        return f'http://{cls.address}:{cls.port}/index.html?' \
               f'host={cls.address}&port={cls.projector_port}'

    def is_empty_path(self) -> bool:
        """Checks if current path is empty."""
        return not self.path or self.path == '/'

    def path_contains_index_html(self) -> bool:
        """Checks if path contains index.html"""
        return self.path.find('index.html') != -1

    def path_contains_projector_port(self) -> bool:
        """Checks if path contains projector port."""
        return self.path.find(f'port={NoLogServer.projector_port}') != -1

    def need_redirect(self) -> bool:
        """Checks if we need redirect request."""
        if self.is_empty_path():
            return True

        if not self.path_contains_index_html():
            return False

        return not self.path_contains_projector_port()


class HttpServerProcess(Process):
    """Http server process class."""

    def __init__(self, run_config: RunConfig, directory: str) -> None:
        super().__init__(daemon=True)
        self.run_config = run_config
        self.directory = directory
        self.httpd: Optional[socketserver.BaseServer] = None

    def run(self) -> None:
        chdir(self.directory)
        NoLogServer.init_with(self.run_config)
        socketserver.TCPServer.allow_reuse_address = True

        with socketserver.TCPServer((self.run_config.http_address,
                                     self.run_config.http_port),
                                    NoLogServer) as httpd:
            if is_secure(self.run_config):
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(get_http_crt_file(self.run_config.name),
                                        get_http_key_file(self.run_config.name))
                httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

            self.httpd = httpd

            try:
                httpd.serve_forever()
            except socket.error:
                httpd.shutdown()
                httpd.server_close()
                self.httpd = None

    def terminate(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

        super().terminate()
