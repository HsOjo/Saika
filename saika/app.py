import importlib
import os
import pkgutil
import sys
import traceback

from flask import Flask
from werkzeug.serving import is_running_from_reloader

from . import hard_code
from .config import Config
from .const import Const
from .database import db, migrate
from .environ import Environ
from .meta_table import MetaTable


class SaikaApp(Flask):
    def __init__(self, **kwargs):
        super().__init__(self.__class__.__module__, **kwargs)
        if self.debug and not is_running_from_reloader():
            return

        try:
            self._init_env()
            self._init_config()
            self._init_app()

            self.controllers = []
            self._import_modules()
            self._init_controllers()
        except:
            traceback.print_exc(file=sys.stderr)

    def _init_env(self):
        if Environ.app is not None:
            raise Exception('SaikaApp was created.')

        Environ.app = self
        Environ.program_path = os.path.join(self.root_path, '../../dockore')
        Environ.config_path = os.path.join(Environ.program_path, Const.config_file)
        Environ.data_path = os.path.join(Environ.program_path, Const.data_dir)

    def _init_config(self):
        Config.load(Environ.config_path)
        cfg = Config.merge()
        self.config.from_mapping(cfg)

    def _init_app(self):
        db.init_app(self)
        migrate.init_app(self, db)
        self.callback_init_app()

    def _init_controllers(self):
        controller_classes = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_CONTROLLER_CLASSES, [])
        self.controllers = [cls(self) for cls in controller_classes]

    def _import_modules(self):
        module = self.__class__.__module__
        sub_modules = list(pkgutil.iter_modules([module], '%s.' % module))
        sub_modules = [i.name for i in sub_modules if i.ispkg]
        for i in sub_modules:
            importlib.import_module(i)

    def callback_init_app(self):
        pass
