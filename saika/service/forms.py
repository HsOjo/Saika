from wtforms import StringField, FieldList
from wtforms.validators import DataRequired

from saika.form import Form
from saika.form.fields import DataField
from .operators import Operators


class FieldOperateForm(Form):
    field = StringField(validators=[DataRequired()])
    operate = StringField(validators=[DataRequired()])
    args = DataField()

    def operator(self, model):
        field = getattr(model, self.field.data, None)
        if field is None:
            return None

        operator = Operators.get(self.operate.data, None)
        if operator is None:
            return None

        args = self.args.data or []

        if not isinstance(args, list):
            args = [args]

        return operator(field, args)
