from flask_sqlalchemy import BaseQuery
from wtforms import StringField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired

from saika.database import db
from saika.form import Form, JSONForm
from saika.form.fields import DataField
from .operators import Operators


class FieldOperateForm(Form):
    field = StringField(validators=[DataRequired()])
    operate = StringField(validators=[DataRequired()])
    args = DataField()

    def operator(self, model):
        relationship_models = []

        field = model
        for index, field_str in enumerate(self.field.data.split('.')):
            if index > 0:
                field = db.get_relationship_class(field)
                if field != model:
                    relationship_models.append(field)
            field = getattr(field, field_str, None)
            if field is None:
                return None

        operator = Operators.get(self.operate.data, None)
        if operator is None:
            return None

        args = self.args.data or []

        if not isinstance(args, list):
            args = [args]

        return operator(field, args), set(relationship_models)


class PaginateForm(JSONForm):
    page = IntegerField(default=1)
    per_page = IntegerField(default=10)


class AdvancedPaginateForm(PaginateForm):
    filters = FieldList(FormField(FieldOperateForm))
    orders = FieldList(FormField(FieldOperateForm))

    def query(self, model, query=None):
        if query is None:
            query = model.query  # type: BaseQuery

        relationship_models = []

        filters = []
        orders = []

        def handle_operate_fields(fields, dest):
            nonlocal relationship_models
            for form in fields:
                result = form.operator(model)
                if result is not None:
                    [operator, models] = result
                    relationship_models += models
                    dest.append(operator)

        handle_operate_fields(self.filters, filters)
        handle_operate_fields(self.orders, orders)

        if relationship_models:
            for relationship_model in set(relationship_models):
                query = query.join(relationship_model)
        if filters:
            query = query.filter(*filters)
        if orders:
            query = query.order_by(*orders)

        return query
