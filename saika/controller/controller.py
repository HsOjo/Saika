import re

from flask import Blueprint, Flask, abort, redirect, flash, url_for, send_file, send_from_directory, make_response

from saika import hard_code
from saika.context import Context
from saika.meta_table import MetaTable


class Controller:
    abort = abort
    redirect = redirect
    flash = flash
    url_for = url_for
    send_file = send_file
    send_from_directory = send_from_directory
    make_response = make_response

    def __init__(self, app):
        name = self.__class__.__name__.replace('Controller', '')
        self._name = re.sub('[A-Z]', lambda x: '_' + x.group().lower(), name).lstrip('_')
        self._import_name = self.__class__.__module__

        self._blueprint = Blueprint(self._name, self._import_name)
        self._register(app)

    @property
    def blueprint(self):
        return self._blueprint

    @property
    def context(self):
        return Context

    @property
    def request(self):
        return Context.request

    @property
    def form(self):
        form = Context.g_get(hard_code.MK_FORM)
        return form

    @property
    def options(self):
        options = MetaTable.get(self.__class__, hard_code.MK_OPTIONS, {})  # type: dict
        return options

    @property
    def view_function_options(self):
        options = MetaTable.all(Context.get_view_function())  # type: dict
        return options

    def _register_methods(self):
        keeps = dir(Controller)
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
                    self._blueprint.add_url_rule(
                        rule=meta[hard_code.MK_RULE_STR],
                        methods=meta[hard_code.MK_METHODS],
                        view_func=_f
                    )

    def _register(self, app):
        app: Flask
        self.callback_before_register()
        self._register_methods()
        app.register_blueprint(self._blueprint, **self.options)

    def callback_before_register(self):
        pass
