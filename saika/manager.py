from flask_migrate import MigrateCommand
from flask_script import Manager, Server

from .app import SaikaApp, make_context
from .socket_io import socket_io


class SocketServer(Server):
    def __call__(self, app, host, port, use_debugger, use_reloader,
                 threaded, processes, passthrough_errors, ssl_crt, ssl_key):
        kwargs = dict(debug=use_debugger, use_reloader=use_reloader, certfile=ssl_crt, keyfile=ssl_key)
        for k, v in list(kwargs.items()):
            if v is None:
                kwargs.pop(k)

        socket_io.run(app, host, port, log_output=True, **kwargs)


def init_manager(app: SaikaApp, **kwargs):
    manager = Manager(app, **kwargs)
    manager.add_command('db', MigrateCommand)
    manager.shell(make_context)
    if len(app.sio_controllers):
        manager.add_command('runserver', SocketServer())

    return manager
