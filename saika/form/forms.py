from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from wtforms import StringField, IntegerField, FieldList, BooleanField, FloatField, FormField
from wtforms_json import flatten_json

from saika.context import Context

FORM_TYPE_ARGS = 'args'
FORM_TYPE_FORM = 'form'
FORM_TYPE_JSON = 'json'
FORM_TYPE_REST = 'rest'


class Form(FlaskForm):
    data: dict
    errors: dict
    type = FORM_TYPE_FORM

    def inject_obj_data(self, obj):
        for k in self.data:
            value = getattr(obj, k, None)
            if value is not None:
                field = getattr(self, k, None)
                if hasattr(field, 'data'):
                    field.data = value

    def dump_fields(self):
        fields = {}

        types_mapping = {
            StringField: str,
            IntegerField: int,
            FieldList: list,
            BooleanField: bool,
            FloatField: float,
            FormField: dict,
        }

        for key, field in self._fields.items():
            required = False
            for i in field.validators:
                if hasattr(i, 'field_flags') and 'required' in i.field_flags:
                    required = True
                    break

            fields[key] = dict(
                label=field.label.text,
                type=types_mapping.get(type(field), object),
                default=field.default,
                description=field.description,
                required=required,
            )

        return fields


class ArgsForm(Form):
    type = FORM_TYPE_ARGS

    def __init__(self, **kwargs):
        super().__init__(MultiDict(Context.request.args), **kwargs)


class ViewArgsForm(Form):
    type = FORM_TYPE_REST

    def __init__(self, **kwargs):
        super().__init__(MultiDict(Context.request.view_args), **kwargs)


class JSONForm(Form):
    type = FORM_TYPE_JSON

    def __init__(self, **kwargs):
        formdata = Context.request.get_json()
        if formdata is not None:
            formdata = MultiDict(flatten_json(self.__class__, formdata))
        super().__init__(formdata, **kwargs)
