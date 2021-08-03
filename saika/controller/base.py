import re

from saika import hard_code
from saika.meta_table import MetaTable


class ControllerBase:
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

    def instance_register(self, *args, **kwargs):
        pass

    def get_functions(self, cls=None):
        if cls is None:
            cls = ControllerBase

        functions = []

        keeps = dir(cls)
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
