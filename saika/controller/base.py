import re

from flask import Blueprint

from saika import hard_code
from saika.context import Context
from saika.environ import Environ
from saika.meta_table import MetaTable


class ControllerBase:
    def __init__(self):
        name = self.__class__.__name__.replace('Controller', '')
        self._name = re.sub('[A-Z]', lambda x: '_' + x.group().lower(), name).lstrip('_')
        self._import_name = self.__class__.__module__

        self.view_functions = []

        self._blueprint = Blueprint(self._name, self._import_name)
        self._register_methods()

    @property
    def blueprint(self):
        return self._blueprint

    @property
    def name(self):
        return self._name

    @property
    def context(self):
        return Context

    @property
    def request(self):
        return Context.request

    @property
    def options(self):
        options = MetaTable.get(self.__class__, hard_code.MK_OPTIONS, {})  # type: dict
        return options

    @property
    def view_function_options(self):
        options = MetaTable.all(Context.get_view_function())  # type: dict
        return options

    def _register_methods(self):
        if Environ.debug:
            Environ.app.logger.debug(' * Init %s (%s): %a' % (self._import_name, self._name, self.options))

        keeps = dir(ControllerBase)
        for k in dir(self):
            if k in keeps:
                continue

            t = getattr(self.__class__, k, None)
            if isinstance(t, property):
                continue

            _f = f = getattr(self, k)
            if callable(f):
                if hasattr(f, '__func__'):
                    f = f.__func__
                meta = MetaTable.all(f)
                if meta is not None:
                    options = dict()
                    methods = meta.get(hard_code.MK_METHODS)
                    if methods:
                        options['methods'] = methods

                    self._blueprint.add_url_rule(meta[hard_code.MK_RULE_STR], None, _f, **options)
                    self.view_functions.append(f)

                    if Environ.debug:
                        name = _f.__name__
                        if hasattr(_f, '__qualname__'):
                            name = _f.__qualname__
                        Environ.app.logger.debug('   - %s: %a' % (name, options))

    def instance_register(self, *args, **kwargs):
        pass

    def callback_before_register(self):
        pass
