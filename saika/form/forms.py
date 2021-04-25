from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from wtforms_json import flatten_json

from saika.context import Context


class Form(FlaskForm):
    data: dict
    errors: dict


class ArgsForm(Form):
    def __init__(self, **kwargs):
        super().__init__(MultiDict(Context.request.args), **kwargs)


class JSONForm(Form):
    def __init__(self, **kwargs):
        formdata = Context.request.get_json()
        if formdata is not None:
            formdata = MultiDict(flatten_json(self.__class__, formdata))
        super().__init__(formdata, **kwargs)
