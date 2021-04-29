from flask_migrate import MigrateCommand
from flask_script import Manager, Server
from werkzeug.serving import is_running_from_reloader

from .app import SaikaApp, make_context
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
            print(' * Environment: %s\n * Debug mode: %s\n * Running on http://%s:%s/ (Press CTRL+C to quit)' % (
                app.env, 'on' if app.debug else 'off', host, port))

        socket_io.server.eio.async_mode = 'gevent'
        socket_io.run(app, host, port, log_output=True, **kwargs)


def init_manager(app: SaikaApp, **kwargs):
    manager = Manager(app, **kwargs)
    manager.add_command('db', MigrateCommand)
    manager.shell(make_context)
    manager.add_command('runserver', GEventServer())

    return manager
