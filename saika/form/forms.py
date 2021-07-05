from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from wtforms import StringField, IntegerField, FieldList, BooleanField, FloatField, FormField, SelectField
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

        def dump_field(f):
            required = False
            for i in f.validators:
                if hasattr(i, 'field_flags') and 'required' in i.field_flags:
                    required = True
                    break

            data = dict(
                label=f.label.text,
                type=types_mapping.get(type(f), str),
                default=f.default,
                description=f.description,
                required=required,
            )

            if isinstance(f, FormField):
                data.update(form=f.form.dump_fields())
            elif isinstance(f, FieldList):
                data.update(item=dump_field(f.unbound_field.bind(f, f.name)))
            elif isinstance(f, SelectField):
                data.update(type=f.coerce)

            return data

        for key, field in self._fields.items():
            fields[key] = dump_field(field)

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
