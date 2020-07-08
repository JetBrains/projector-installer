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

from os import chdir
from http.server import SimpleHTTPRequestHandler
import socketserver
from multiprocessing import Process


class NoLogServer(SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        try:
            if self.need_redirect():
                self.send_response(301)
                self.send_header('Location', NoLogServer.redirect_url())
                self.end_headers()
            else:
                super(NoLogServer, self).do_GET()
        except:
            pass

    @classmethod
    def redirect_url(cls):
        return f'http://{cls.address}:{cls.http_port}/index.html?port={cls.projector_port}'

    def need_redirect(self):
        ret = not self.path or self.path == "/" or self.path.find("index.html") != -1
        ret = ret and self.path.find(f"port={NoLogServer.projector_port}") == -1
        return ret


class HttpServerProcess(Process):

    def __init__(self, address, port, directory, projector_port):
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
            except:
                httpd.shutdown()
                httpd.server_close()
                self.httpd = None

    def terminate(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

        super(HttpServerProcess, self).terminate()
