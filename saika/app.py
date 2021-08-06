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
from .controller import BaseController, CliController
from .controller.blueprint import BlueprintController
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

        self._controllers = []  # type: List[BaseController]

        try:
            self._init_env()
            self._init_config()
            self._init_app()

            if import_modules:
                self._import_modules()
            self._init_callbacks()
            self._init_context()
            self._init_controllers()
            self._init_cli()
        except:
            traceback.print_exc(file=sys.stderr)

    def _init_env(self):
        if Environ.app is not None:
            raise Exception('SaikaApp was created.')

        Environ.app = self
        Environ.debug = bool(int(os.getenv(hard_code.SAIKA_DEBUG, 0)))

        app_path = sys.modules[self.import_name].__file__
        if os.path.exists(app_path):
            app_dir = os.path.dirname(app_path)
            if '__init__' in os.path.basename(app_path):
                Environ.program_path = os.path.abspath(os.path.join(app_dir, '..'))
            else:
                Environ.program_path = app_dir
        else:
            Environ.program_path = self.root_path

        Environ.config_path = os.path.join(Environ.program_path, Const.config_file)
        Environ.data_path = os.path.abspath(os.path.join(Environ.program_path, Const.data_dir))

    def _init_config(self):
        Config.load()
        cfg = Config.merge()
        self.config.from_mapping(cfg)

    def _init_app(self):
        db.init_app(self)
        migrate.init_app(self, db, render_as_batch=True)
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
        controller_mapping = {
            SocketController: [socket],
            SocketIOController: [socket_io],
            BlueprintController: [self],
            BaseController: [],
        }

        for cls in controller_classes:
            item = cls()
            for controller_cls, controller_args in controller_mapping.items():
                if issubclass(cls, controller_cls):
                    item.register(*controller_args)
                    self._controllers.append(item)
                    break

    def _init_cli(self):
        functions = []
        for controller in self._controllers:
            if isinstance(controller, CliController):
                functions += [f.__func__ for f in controller.functions]

        commands = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_COMMANDS, [])  # type: list

        add_functions = [command for command in commands if command not in functions]
        for f in add_functions:
            self.cli.command()(f)

    def _init_context(self):
        for name, obj in make_context().items():
            self.add_template_global(obj, name)

        items = []
        for key in dir(builtins):
            item = getattr(builtins, key)
            is_builtin = type(item).__name__ == 'builtin_function_or_method'
            if key[0] != '_' and hasattr(item, '__name__') and (is_builtin or re.match('^[a-z]+$', key)):
                items.append(item)

        for item in items:
            self.add_template_global(item)

        self.shell_context_processor(make_context)

    def _import_modules(self, module_name=None):
        if module_name is None:
            module_name = self.__class__.__module__

        module = sys.modules.get(module_name)
        if module is None or module_name.startswith('saika'):
            return
        module_dir = os.path.dirname(module.__file__)

        sub_modules = list(pkgutil.iter_modules([module_dir]))
        sub_pkgs = []
        sub_modules_import = []
        for sub_module in sub_modules:
            if sub_module.ispkg:
                sub_pkgs.append('%s.%s' % (module_name, sub_module.name))
            else:
                sub_module_name_l = sub_module.name.lower()
                for k in ['controller', 'model']:
                    if k in sub_module_name_l:
                        sub_modules_import.append('%s.%s' % (module_name, sub_module.name))

        def import_module(module_name):
            try:
                importlib.import_module(module_name)
            except Exception as e:
                Environ.app.logger.error(e)

        for sub_pkg in sub_pkgs:
            import_module(sub_pkg)
            self._import_modules(sub_pkg)

        for sub_module in sub_modules_import:
            import_module(sub_module)

    def callback_init_app(self):
        pass

    def reload(self):
        if Environ.is_gunicorn():
            os.kill(os.getppid(), signal.SIGHUP)
        else:
            self.logger.warning(' * App Reload: Support reload in gunicorn only.')

    @property
    def controllers(self):
        return self._controllers


def make_context():
    context = dict(Config=Config, Const=Const, Context=Context, db=db, Environ=Environ, MetaTable=MetaTable)
    classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODEL_CLASSES, [])
    for cls in classes:
        context[cls.__name__] = cls
    return context
