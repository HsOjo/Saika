from flask_migrate import MigrateCommand
from flask_script import Manager, Shell

from .app import SaikaApp, make_context


def init_manager(app: SaikaApp, **kwargs):
    manager = Manager(app, **kwargs)
    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(make_context=make_context))
    return manager
