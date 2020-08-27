# Copyright 2000-2020 JetBrains s.r.o.
# Use of this source code is governed by the Apache 2.0 license that can be found
# in the LICENSE file.


"""HTTP server process module."""

from os import chdir
from typing import Any, Optional
from http.server import SimpleHTTPRequestHandler
import socketserver
from multiprocessing import Process
import socket


class NoLogServer(SimpleHTTPRequestHandler):
    """Custom http server class to serve static projector client files."""
    address: str = ''
    http_port: str = ''
    projector_port: str = ''

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
    def redirect_url(cls) -> str:
        """Constructs redirect url."""
        return f'http://{cls.address}:{cls.http_port}/index.html?port={cls.projector_port}'

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

    def __init__(self, address: str, port: int, directory: str, projector_port: int) -> None:
        super().__init__(daemon=True)
        self.address = address
        self.port = port
        self.directory = directory
        self.projector_port = projector_port
        self.httpd: Optional[socketserver.BaseServer] = None

    def run(self) -> None:
        chdir(self.directory)
        NoLogServer.address = self.address
        NoLogServer.http_port = str(self.port)
        NoLogServer.projector_port = str(self.projector_port)
        socketserver.TCPServer.allow_reuse_address = True

        with socketserver.TCPServer((self.address, self.port), NoLogServer) as httpd:
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
