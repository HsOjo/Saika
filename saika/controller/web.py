from flask import abort, redirect, flash, url_for, send_file, send_from_directory, make_response, request

from saika import hard_code
from saika.context import Context
from saika.environ import Environ
from saika.form import Form
from saika.meta_table import MetaTable
from .blueprint import BlueprintController


class WebController(BlueprintController):
    def __init__(self):
        super().__init__()

        self.abort = abort
        self.redirect = redirect
        self.flash = flash
        self.url_for = url_for
        self.send_file = send_file
        self.send_from_directory = send_from_directory
        self.make_response = make_response

    @property
    def request(self):
        return request

    @property
    def context(self):
        return Context

    @property
    def view_function_options(self):
        options = MetaTable.all(Context.get_view_function())  # type: dict
        return options

    @property
    def form(self):
        form = Context.g_get(hard_code.GK_FORM)  # type: Form
        return form

    def _register_functions(self):
        if Environ.debug:
            Environ.app.logger.debug(' * Init %s (%s): %a' % (self.import_name, self.name, self.options))

        for f in self.methods:
            _f = f
            f = getattr(f, '__func__', f)

            meta = MetaTable.all(f)
            if meta is not None:
                options = dict()
                methods = meta.get(hard_code.MK_METHODS)
                if methods:
                    options['methods'] = methods

                self._blueprint.add_url_rule(meta[hard_code.MK_RULE_STR], None, _f, **options)
                self._functions.append(_f)

                if Environ.debug:
                    name = _f.__qualname__
                    Environ.app.logger.debug('   - %s: %a' % (name, options))
