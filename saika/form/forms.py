from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict

from saika.context import Context


class Form(FlaskForm):
    data: dict
    errors: dict


class ArgsForm(Form):
    def __init__(self, **kwargs):
        super().__init__(MultiDict(Context.request.args), **kwargs)
