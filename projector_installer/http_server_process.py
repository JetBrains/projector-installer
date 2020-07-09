#  GNU General Public License version 2
#
#  Copyright (C) 2019-2020 JetBrains s.r.o.
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License version 2 only, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""HTTP server process module."""

from os import chdir
from http.server import SimpleHTTPRequestHandler
import socketserver
from multiprocessing import Process
import socket


class NoLogServer(SimpleHTTPRequestHandler):
    """Custom http server class to serve static projector client files."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        try:
            if self.need_redirect():
                self.send_response(301)
                self.send_header('Location', NoLogServer.redirect_url())
                self.end_headers()
            else:
                super(NoLogServer, self).do_GET()
        except socket.error:
            pass

    @classmethod
    def redirect_url(cls):
        """Constructs redirect url."""
        return f'http://{cls.address}:{cls.http_port}/index.html?port={cls.projector_port}'

    def is_empty_path(self):
        """Checks if current path is empty."""
        return not self.path or self.path == "/"

    def path_contains_index_html(self):
        """Checks if path contains index.html"""
        return self.path.find("index.html") != -1

    def path_contains_projector_port(self):
        """Checks if path contains projector port."""
        return self.path.find(f"port={NoLogServer.projector_port}") != -1

    def need_redirect(self):
        """Checks if we need redirect request."""
        if self.is_empty_path():
            return True

        if not self.path_contains_index_html():
            return False

        return not self.path_contains_projector_port()


class HttpServerProcess(Process):
    """Http server process class."""

    def __init__(self, address, port, directory, projector_port) -> object:
        super(HttpServerProcess, self).__init__(daemon=True)
        self.address = address
        self.port = port
        self.directory = directory
        self.projector_port = projector_port
        self.httpd = None

    def run(self):
        chdir(self.directory)
        NoLogServer.address = self.address
        NoLogServer.http_port = self.port
        NoLogServer.projector_port = self.projector_port
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

        super(HttpServerProcess, self).terminate()
