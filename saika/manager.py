from flask_migrate import MigrateCommand
from flask_script import Manager, Shell

from . import hard_code
from .app import SaikaApp


def make_shell_context():
    from saika import Config, Const, Context, db, Environ, MetaTable
    context = dict(Config=Config, Const=Const, Context=Context, db=db, Environ=Environ, MetaTable=MetaTable)
    classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODEL_CLASSES, [])
    for cls in classes:
        context[cls.__name__] = cls
    return context


def init_manager(app: SaikaApp, **kwargs):
    manager = Manager(app, **kwargs)
    manager.add_command('db', MigrateCommand)
    manager.add_command('shell', Shell(make_context=make_shell_context))
    return manager
