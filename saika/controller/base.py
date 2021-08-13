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

    @property
    def attrs(self):
        attrs = {}
        attrs.update(self.__class__.__dict__)
        attrs.update(self.__dict__)
        attrs = {k: getattr(self, k) for k, v in attrs.items() if k[0] != '_' and not isinstance(v, property)}
        return attrs

    @property
    def methods(self):
        return list(self.attrs.values())

    def register(self, *args, **kwargs):
        self.callback_before_register()

    def callback_before_register(self):
        pass
