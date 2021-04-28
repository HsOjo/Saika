from flask import abort, redirect, flash, url_for, send_file, send_from_directory, make_response, Flask

from saika import hard_code
from saika.context import Context
from .controller import Controller


class WebController(Controller):
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
    def form(self):
        form = Context.g_get(hard_code.GK_FORM)
        return form

    def register(self, app: Flask):
        self.callback_before_register()
        app.register_blueprint(self.blueprint, **self.options)

    def callback_before_register(self):
        pass
