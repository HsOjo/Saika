import logging
import multiprocessing

import termcolor
from flask import Response
from gunicorn.app.base import BaseApplication

from saika.context import Context
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
        logger = logging.getLogger('gunicorn.error')

        @self.app.after_request
        def print_log(resp: Response):
            f_log = logger.error if resp.status_code != 200 else logger.info

            req = Context.request
            color = 'yellow' if resp.status_code != 200 else 'green'

            f_log('%(remote_addr)s - "%(request)s" %(status_code)s' % dict(
                remote_addr=req.remote_addr,
                request=termcolor.colored('%(method)s %(path)s %(protocol)s' % dict(
                    method=req.method,
                    path=req.path,
                    protocol=req.environ.get('SERVER_PROTOCOL'),
                ), color),
                status_code=resp.status_code,
            ))
            return resp

        GunicornApp(app=self.app, config=dict(
            bind='%s:%s' % (host, port),
            workers=multiprocessing.cpu_count() * 2 + 1,
            worker_class='saika.worker',
            reload=use_reloader,
            certfile=ssl_crt,
            keyfile=ssl_key,
            **kwargs,
        )).run()
