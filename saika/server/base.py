import saika


class BaseServer:
    def __init__(self, app):
        self.app = app  # type: saika.SaikaApp

    def run(self, host, port, debug, use_reloader, ssl_crt, ssl_key, **kwargs):
        pass
