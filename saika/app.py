import builtins
import importlib
import os
import re
import signal
import sys
import traceback
from typing import List, Optional

from flask import Flask
from flask.cli import FlaskGroup

from . import hard_code, common
from .config import Config, BaseConfig, ConfigProvider, FileProvider
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
    _init_args = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            obj = object.__new__(cls)
            cls._instance = obj
        return cls._instance

    def __init__(self, import_name=None, import_modules=True, **kwargs):
        if Environ.app is self:
            self.import_name = import_name
            return

        if import_name is None:
            if self.__class__ is SaikaApp:
                raise Exception('Must set import_name.')
            import_name = self.__class__.__module__

        self._module = importlib.import_module(import_name)
        if self._module.__spec__.origin is None:
            self._module.__spec__ = None
        self._sub_modules = []

        if import_name == '__main__':
            os.environ.setdefault('FLASK_APP', os.path.basename(self._module.__file__))

        super().__init__(import_name, **kwargs)

        self.set_form_validate_default = set_form_validate_default
        self.set_fork_killer = set_fork_killer

        self._controllers = []  # type: List[BaseController]
        self._configs = {}  # type: dict

        self._config_provider_default = None  # type: Optional[ConfigProvider]

        try:
            self._init_env()

            if import_modules:
                self._import_modules()

            self._init_configs()
            self._init_app()
            self._init_callbacks()
            self._init_context()
            self._init_controllers()
            self._init_cli()
        except:
            traceback.print_exc(file=sys.stderr)

    def _init_env(self):
        if Environ.app is not None:
            raise Exception('''%s doesn't support multiple instance.''' % SaikaApp.__name__)

        Environ.app = self
        Environ.debug = bool(int(os.getenv(hard_code.SAIKA_DEBUG, 0)))

        if Environ.is_pyinstaller():
            Environ.program_dir = os.path.dirname(sys.argv[0])
        else:
            app_path = importlib.import_module(self.import_name).__file__
            if os.path.exists(app_path):
                app_dir = os.path.dirname(app_path)
                if '__init__' in os.path.basename(app_path):
                    Environ.program_dir = os.path.abspath(os.path.join(app_dir, '..'))
                else:
                    Environ.program_dir = app_dir
            else:
                Environ.program_dir = self.root_path

        self.set_data_dir()

    def set_data_dir(self, data_dir=None):
        if data_dir is None:
            data_dir = os.getenv(
                hard_code.SAIKA_DATA_DIR,
                os.path.abspath(os.path.join(Environ.program_dir, Const.data_dir))
            )

        Environ.data_dir = data_dir
        Environ.config_path = os.path.join(Environ.data_dir, Const.config_file)
        os.makedirs(Environ.data_dir, exist_ok=True)

        self.load_configs()

    def _init_configs(self):
        if self._config_provider_default is None:
            self._config_provider_default = FileProvider(lambda: Environ.config_path)

        config_classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_CONFIG_CLASSES, [])
        for cls in config_classes:
            if issubclass(cls, BaseConfig):
                cfg = cls()
                provider = MetaTable.get(cls, hard_code.MK_CONFIG_PROVIDER)
                if provider is None:
                    provider = self._config_provider_default
                cfg.set_provider(provider)
                cfg.refresh()
                self._configs[cls] = cfg

        self.load_configs()

    def _init_app(self):
        db.init_app(self)
        migrate.init_app(self, db, render_as_batch=True)
        cors.init_app(self)
        socket_io.init_app(self)
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
                functions += [
                    getattr(f, '__func__', f)
                    for f in controller.functions
                ]

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
            if not key.startswith('_') and hasattr(item, '__name__') and (is_builtin or re.match('^[a-z]+$', key)):
                items.append(item)

        for item in items:
            self.add_template_global(item)

        self.shell_context_processor(make_context)

    def _import_modules(self):
        app_module = importlib.import_module(self.__class__.__module__)
        if app_module is None or app_module.__name__.startswith(Const.project_name.lower()):
            return

        keywords = ['controller', 'model', 'config', 'service']
        for module_info in common.walk_modules(app_module, to_dict=True):
            endpoint = module_info['endpoint']
            import_need = module_info['is_pkg']

            if not import_need:
                for keyword in keywords:
                    if keyword in endpoint:
                        import_need = True
                        break

            if import_need:
                importlib.import_module(endpoint)

            self._sub_modules.append(endpoint)

    def callback_init_app(self):
        pass

    def restart(self):
        if Environ.is_gunicorn():
            os.kill(os.getppid(), signal.SIGHUP)
        else:
            self.logger.warning(' * App Reload: Support reload in gunicorn only.')

    @property
    def controllers(self):
        return self._controllers

    @property
    def configs(self):
        return self._configs

    @property
    def module(self):
        return self._module

    @property
    def sub_modules(self):
        return self._sub_modules

    @property
    def ext_modules(self):
        modules = []
        sub_modules_set = set(self.sub_modules)

        def check_name(name: str):
            module_parts = name.split('.')
            module_root = module_parts[0]
            if module_root in sys.builtin_module_names:
                return False
            for module_part in module_parts:
                if module_part.startswith('_'):
                    return False
            return True

        for module_name, module in sys.modules.items():
            module_pkg = getattr(module, '__package__', None)
            if module_pkg is not None and module_name.find(module_pkg) == 0:
                module_path = getattr(module, '__file__', None)
                if not module_path or (module_pkg == '' and '-packages' not in module_path):
                    continue

                if module_name not in sub_modules_set and check_name(module_name):
                    if module_name.replace('.', '/') in module_path:
                        modules.append(module_name)

        return modules

    @property
    def flask_cli(self):
        with self.app_context():
            from flask_migrate.cli import db as db_cli
            cli = FlaskGroup()
            cli.add_command(db_cli)
            return cli

    def load_configs(self):
        for config in self._configs.values():
            options = config.merge()
            if options is not None:
                self.config.update(options)


def make_context():
    context = dict(Config=Config, Const=Const, Context=Context, db=db, Environ=Environ, MetaTable=MetaTable)
    classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODEL_CLASSES, [])
    for cls in classes:
        context[cls.__name__] = cls
    return context
