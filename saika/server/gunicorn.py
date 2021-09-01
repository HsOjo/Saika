import multiprocessing

from gunicorn.app.base import BaseApplication

from saika.server.base import BaseServer


class GunicornApp(BaseApplication):
    def init(self, parser, opts, args):
        pass

    def __init__(self, app, config):
        self._config = config
        self._app = app
        super().__init__()

    def load(self):
        return self._app

    def load_config(self):
        for k, v in self._config.items():
            self.cfg.set(k, v)


class Gunicorn(BaseServer):
    def run(self, host, port, debug, use_reloader, ssl_crt, ssl_key, **kwargs):
        kwargs.setdefault('timeout', 0)
        GunicornApp(app=self.app, config=dict(
            bind='%s:%s' % (host, port),
            workers=multiprocessing.cpu_count() * 2 + 1,
            worker_class='saika.worker',
            reload=use_reloader,
            certfile=ssl_crt,
            keyfile=ssl_key,
            **kwargs,
        )).run()
