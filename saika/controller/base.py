import re

from saika import hard_code
from saika.meta_table import MetaTable


class BaseController:
    def __init__(self):
        name = self.__class__.__name__.replace('Controller', '')
        self._name = re.sub('[A-Z]', lambda x: '_' + x.group().lower(), name).lstrip('_')
        self._import_name = self.__class__.__module__

    @property
    def name(self):
        return self._name

    @property
    def import_name(self):
        return self._import_name

    @property
    def options(self):
        options = MetaTable.get(self.__class__, hard_code.MK_OPTIONS, {})  # type: dict
        return options

    def get_functions(self, cls_base=None):
        if cls_base is None:
            cls_base = BaseController

        functions = []

        keeps = dir(cls_base)
        for k in dir(self):
            if k in keeps:
                continue

            t = getattr(self.__class__, k, None)
            if isinstance(t, property):
                continue

            f = getattr(self, k)
            if callable(f):
                functions.append(f)

        return functions

    def register(self, *args, **kwargs):
        self.callback_before_register()

    def callback_before_register(self):
        pass
