import sys
import time

import termcolor
from flask import Response
from werkzeug.serving import is_running_from_reloader

from saika.socket_io import socket_io
from saika.const import Const
from saika.context import Context
from .base import BaseServer


class Gevent(BaseServer):
    def run(self, host, port, debug, use_reloader, ssl_crt, ssl_key, **kwargs):
        app = self.app

        options = dict(debug=debug, use_reloader=use_reloader, certfile=ssl_crt, keyfile=ssl_key, **kwargs)
        for k, v in list(options.items()):
            if v is None:
                options.pop(k)

        if not use_reloader or is_running_from_reloader():
            print(' * Serving %s "%s"' % (app.__class__.__name__, app.import_name))
            print('   - %(project_name)s Version: %(version)s' % Const.__dict__)
            print(' * Environment: %s' % app.env)
            if app.env == 'production':
                print(termcolor.colored(
                    "   WARNING: This is a development server. "
                    "Do not use it in a production deployment.\n"
                    "   Use a production WSGI server instead.",
                    color="red")
                )
            print(' * Debug mode: %s' % ('on' if app.debug else 'off'))
            print(' * Running on http://%s:%s/ (Press CTRL+C to quit)' % (host, port))

        @app.after_request
        def print_log(resp: Response):
            req = Context.request
            color = 'yellow' if resp.status_code != 200 else 'green'
            print('%(remote_addr)s - - [%(time)s] "%(request)s" %(status_code)s' % dict(
                remote_addr=req.remote_addr,
                time=time.strftime('%d/%b/%Y %H:%M:%S'),
                request=termcolor.colored('%(method)s %(path)s %(protocol)s' % dict(
                    method=req.method,
                    path=req.path,
                    protocol=req.environ.get('SERVER_PROTOCOL'),
                ), color),
                status_code=resp.status_code,
            ), file=sys.stderr)
            return resp

        socket_io.server.eio.async_mode = 'gevent'
        try:
            socket_io.run(app, host, port, log_output=True, **options)
        except KeyboardInterrupt:
            pass
