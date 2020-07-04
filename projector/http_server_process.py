import os
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
        os.chdir(self.directory)
        NoLogServer.address = self.address
        NoLogServer.http_port = self.port
        NoLogServer.projector_port = self.projector_port

        with socketserver.TCPServer((self.address, self.port), NoLogServer) as httpd:
            self.httpd = httpd

            try:
                httpd.serve_forever()
            except:
                httpd.shutdown()

    def terminate(self) -> None:
        if self.httpd:
            self.httpd.shutdown()

        super(HttpServerProcess, self).terminate()
