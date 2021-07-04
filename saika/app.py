import builtins
import importlib
import os
import pkgutil
import re
import signal
import sys
import traceback
from typing import List

from flask import Flask

from . import hard_code
from .config import Config
from .const import Const
from .context import Context
from .controller import WebController
from .cors import cors
from .database import db, migrate
from .environ import Environ
from .form import set_form_validate_default
from .meta_table import MetaTable
from .socket import socket, SocketController
from .socket_io import socket_io, SocketIOController
from .workers import set_fork_killer


class SaikaApp(Flask):
    def __init__(self, import_name=None, import_modules=True, **kwargs):
        if import_name is None:
            if self.__class__ is SaikaApp:
                raise Exception('Must set import_name.')
            import_name = self.__class__.__module__

        super().__init__(import_name, **kwargs)

        self.set_form_validate_default = set_form_validate_default
        self.set_fork_killer = set_fork_killer

        self.web_controllers = []  # type: List[WebController]
        self.socket_controllers = []  # type: List[SocketController]
        self.sio_controllers = []  # type: List[SocketIOController]

        try:
            self._init_env()
            self._init_config()
            self._init_app()

            if import_modules:
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
        Environ.debug = bool(os.getenv(hard_code.SAIKA_DEBUG))

        app_path = sys.modules[self.import_name].__file__
        if os.path.exists(app_path):
            app_dir = os.path.dirname(app_path)
            if '__init__' in os.path.basename(app_path):
                Environ.program_path = os.path.join(app_dir, '..')
            else:
                Environ.program_path = app_dir
        else:
            Environ.program_path = self.root_path

        Environ.config_path = os.path.join(Environ.program_path, Const.config_file)
        Environ.data_path = os.path.abspath(os.path.join(Environ.program_path, Const.data_dir))

    def _init_config(self):
        cfg = Config.merge()
        self.config.from_mapping(cfg)

    def _init_app(self):
        db.init_app(self)
        migrate.init_app(self, db)
        cors.init_app(self, **(Config.section('cors') or dict(
            supports_credentials=True,
        )))
        socket_io.init_app(self, **(Config.section('socket_io') or dict(
            cors_allowed_origins='*',
        )))
        socket.init_app(self)
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
                item.instance_register(self)
                self.web_controllers.append(item)
            elif issubclass(cls, SocketController):
                item = cls()
                item.instance_register(socket)
                self.socket_controllers.append(item)
            elif issubclass(cls, SocketIOController):
                options = MetaTable.get(cls, hard_code.MK_OPTIONS)
                item = cls(namespace=options.pop(hard_code.MK_URL_PREFIX, None))
                socket_io.on_namespace(item)
                self.sio_controllers.append(item)

    def _init_context(self):
        for name, obj in self.make_context().items():
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

    @staticmethod
    def make_context():
        context = dict(Config=Config, Const=Const, Context=Context, db=db, Environ=Environ, MetaTable=MetaTable)
        classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODEL_CLASSES, [])
        for cls in classes:
            context[cls.__name__] = cls
        return context

    def reload(self):
        if Environ.is_gunicorn():
            os.kill(os.getppid(), signal.SIGHUP)
        else:
            self.logger.warning(' * App Reload: Support reload in gunicorn only.')
