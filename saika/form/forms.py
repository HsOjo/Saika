from flask_wtf.form import _Auto, FlaskForm
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
    form_type = FORM_TYPE_FORM

    def __init__(self, formdata=_Auto, **kwargs):
        if isinstance(formdata, dict):
            formdata = MultiDict(formdata)
        super().__init__(formdata, **kwargs)

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

        def field_flags(f):
            flags = []
            for validator in f.validators:
                if hasattr(validator, 'field_flags'):
                    flags += validator.field_flags

            return flags

        def dump_field(f):
            flags = field_flags(f)
            if isinstance(f, SelectField):
                required = 'optional' not in flags
            else:
                required = 'required' in flags

            type_ = types_mapping.get(type(f), object)
            if type_ is object:
                for cls in types_mapping:
                    if issubclass(type(f), cls):
                        type_ = types_mapping[cls]

            label = str(f.label.text).strip()
            data = dict(
                label=label,
                type=type_,
                default=f.default,
                description=f.description,
                required=required,
            )

            if isinstance(f, FormField):
                data.update(form=f.form.dump_fields())
            elif isinstance(f, FieldList):
                data.update(item=dump_field(f.append_entry()))
            elif isinstance(f, SelectField):
                data.update(type=f.coerce)

            return data

        for key, field in self._fields.items():
            fields[key] = dump_field(field)

        return fields


class ArgsForm(Form):
    form_type = FORM_TYPE_ARGS

    def __init__(self, **kwargs):
        super().__init__(Context.request.args, **kwargs)


class ViewArgsForm(Form):
    form_type = FORM_TYPE_REST

    def __init__(self, **kwargs):
        super().__init__(Context.request.view_args, **kwargs)


class JSONForm(Form):
    form_type = FORM_TYPE_JSON

    def __init__(self, **kwargs):
        formdata = Context.request.get_json()
        if formdata is not None:
            formdata = flatten_json(self.__class__, formdata)

        super().__init__(formdata, **kwargs)
