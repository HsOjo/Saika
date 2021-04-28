import builtins
import importlib
import os
import pkgutil
import re
import sys
import traceback

from flask import Flask

from . import hard_code
from .config import Config
from .const import Const
from .context import Context
from .controller import WebController
from .cors import cors
from .database import db, migrate
from .environ import Environ
from .meta_table import MetaTable
from .socket_io import socket_io, SocketIOController
from .sockets import sockets, SocketController


def make_context():
    context = dict(Config=Config, Const=Const, Context=Context, db=db, Environ=Environ, MetaTable=MetaTable)
    classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODEL_CLASSES, [])
    for cls in classes:
        context[cls.__name__] = cls
    return context


class SaikaApp(Flask):
    def __init__(self, **kwargs):
        super().__init__(self.__class__.__module__, **kwargs)

        self.web_controllers = []
        self.socket_controllers = []
        self.sio_controllers = []

        try:
            self._init_env()
            print(' * Initializing Saika-%s "%s"' % (Const.version, self.import_name))
            self._init_config()
            self._init_app()

            self._import_modules()
            self._init_callbacks()
            self._init_context()
            self._init_controllers()
        except:
            traceback.print_exc(file=sys.stderr)

    def _init_env(self):
        if Environ.app is not None:
            raise Exception('SaikaApp was created.')

        Environ.app = self
        Environ.program_path = os.path.join(self.root_path, '..')
        Environ.config_path = os.path.join(Environ.program_path, Const.config_file)
        Environ.data_path = os.path.join(Environ.program_path, Const.data_dir)

    def _init_config(self):
        Config.load(Environ.config_path)
        cfg = Config.merge()
        self.config.from_mapping(cfg)

    def _init_app(self):
        db.init_app(self)
        migrate.init_app(self, db)
        cors.init_app(self)
        socket_io.init_app(self, cors_allowed_origins='*')
        sockets.init_app(self)
        self.callback_init_app()

    def _init_callbacks(self):
        for f in MetaTable.get(hard_code.MI_CALLBACK, hard_code.MK_BEFORE_APP_REQUEST, []):
            self.before_request(f)
        for f in MetaTable.get(hard_code.MI_CALLBACK, hard_code.MK_BEFORE_APP_FIRST_REQUEST, []):
            self.before_first_request(f)
        for f in MetaTable.get(hard_code.MI_CALLBACK, hard_code.MK_AFTER_APP_REQUEST, []):
            self.after_request(f)

    def _init_controllers(self):
        controller_classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_CONTROLLER_CLASSES, [])
        for cls in controller_classes:
            if issubclass(cls, WebController):
                item = cls()
                item.register(self)
                self.web_controllers.append(item)
            elif issubclass(cls, SocketController):
                item = cls()
                item.register(sockets)
                self.socket_controllers.append(item)
            elif issubclass(cls, SocketIOController):
                options = MetaTable.get(cls, hard_code.MK_OPTIONS)
                item = cls(namespace=options.pop('url_prefix', None))
                socket_io.on_namespace(item)
                self.sio_controllers.append(item)

    def _init_context(self):
        for name, obj in make_context().items():
            self.add_template_global(obj, name)

        items = []
        for key in dir(builtins):
            item = getattr(builtins, key)
            type_name = type(item).__name__
            if key[0] != '_' and hasattr(item, '__name__') and (
                    type_name == 'builtin_function_or_method' or re.match('^[a-z]+$', key)):
                items.append(item)

        for item in items:
            self.add_template_global(item)

    def _import_modules(self):
        module = self.__class__.__module__
        sub_modules = list(pkgutil.iter_modules([module], '%s.' % module))
        sub_modules = [i.name for i in sub_modules if i.ispkg]
        for i in sub_modules:
            importlib.import_module(i)

    def callback_init_app(self):
        pass
