import click
from flask_migrate import MigrateCommand
from flask_script import Manager

from .app import SaikaApp
from .environ import Environ
from .gevent_server import GEventServer


def init_manager(app: SaikaApp, **kwargs):
    manager = Manager(app, **kwargs)
    manager.add_command('db', MigrateCommand)
    manager.shell(app.make_context)
    if not Environ.debug:
        manager.add_command('runserver', GEventServer())
    else:
        click.secho(' * Saika Debug: Websocket is disabled now.', fg="red")

    return manager
