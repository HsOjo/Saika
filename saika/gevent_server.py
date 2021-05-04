import time

import click
from flask import Response
from flask_script import Server
from termcolor import colored
from werkzeug.serving import is_running_from_reloader

from .app import SaikaApp
from .const import Const
from .context import Context
from .environ import Environ
from .socket_io import socket_io


class GEventServer(Server):
    def __call__(self, app: SaikaApp, host, port, use_debugger, use_reloader,
                 threaded, processes, passthrough_errors, ssl_crt, ssl_key):
        kwargs = dict(debug=use_debugger, use_reloader=use_reloader, certfile=ssl_crt, keyfile=ssl_key)
        for k, v in list(kwargs.items()):
            if v is None:
                kwargs.pop(k)

        if use_reloader is None:
            use_reloader = app.debug

        if not use_reloader or is_running_from_reloader():
            click.echo(' * Serving Saika "%s"' % (Environ.app.import_name))
            click.echo('   - Saika Version: %s' % Const.version)
            click.echo(' * Environment: %s' % app.env)
            if app.env == 'production':
                click.secho(
                    "   WARNING: This is a development server. "
                    "Do not use it in a production deployment.",
                    fg="red",
                )
                click.secho("   Use a production WSGI server instead.", dim=True)
            click.echo(' * Debug mode: %s' % ('on' if app.debug else 'off'))
            click.echo(' * Running on http://%s:%s/ (Press CTRL+C to quit)' % (host, port))

        @app.after_request
        def print_log(resp: Response):
            req = Context.request
            color = 'yellow' if resp.status_code != 200 else 'grey'
            click.secho('%(remote_addr)s - - [%(time)s] "%(request)s" %(status_code)s' % dict(
                remote_addr=req.remote_addr,
                time=time.strftime('%d/%b/%Y %H:%M:%S'),
                request=colored('%(method)s %(path)s %(protocol)s' % dict(
                    method=req.method,
                    path=req.path,
                    protocol=req.environ.get('SERVER_PROTOCOL'),
                ), color),
                status_code=resp.status_code,
            ), err=True)
            return resp

        socket_io.server.eio.async_mode = 'gevent'
        try:
            socket_io.run(app, host, port, log_output=True, **kwargs)
        except KeyboardInterrupt:
            pass
