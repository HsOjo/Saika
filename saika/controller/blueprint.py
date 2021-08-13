from flask import Blueprint

from .base import BaseController


class BlueprintController(BaseController):
    def __init__(self):
        super().__init__()
        self._blueprint = Blueprint(self.name, self.import_name)
        self._functions = []

    @property
    def blueprint(self):
        return self._blueprint

    @property
    def functions(self):
        return self._functions

    def register(self, app):
        super().register()
        self._register_functions()
        app.register_blueprint(self._blueprint, **self.options)

    def _register_functions(self):
        pass
