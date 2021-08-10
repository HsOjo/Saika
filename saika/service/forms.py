from flask_sqlalchemy import BaseQuery
from sqlalchemy.sql import Join
from wtforms import StringField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired

from saika import common
from saika.database import db
from saika.form import Form, JSONForm
from saika.form.fields import DataField
from .operators import Operators


class FieldOperateForm(Form):
    field = StringField(validators=[DataRequired()])
    operate = StringField(validators=[DataRequired()])
    args = DataField()

    def operator(self, model):
        relationship_objs = []

        field = model
        # 根据表单field字段获取模型所关联的字段，如 'category.id' -> Category.id
        for index, field_str in enumerate(self.field.data.split('.')):
            # 第一次循环，field为模型本身，跳过
            if index > 0:
                primary, secondary = db.get_relationship_objs(field)
                if isinstance(secondary, Join):
                    relationship_objs.append(secondary)
                else:
                    if secondary is not None:
                        relationship_objs.append(secondary)
                    relationship_objs.append(primary)
                field = primary
            # 从模型中获取对应字段
            field = getattr(field, field_str, None)
            if field is None:
                return None

        operator = Operators.get(self.operate.data, None)
        if operator is None:
            return None

        args = self.args.data

        if not isinstance(args, list):
            args = [args]

        relationship_objs = common.list_group_by(relationship_objs)
        for i in reversed(relationship_objs):
            if i is None or i == model:
                relationship_objs.remove(i)

        return operator(field, args), relationship_objs


class PaginateForm(JSONForm):
    page = IntegerField(default=1)
    per_page = IntegerField(default=10)


class AdvancedPaginateForm(PaginateForm):
    filters = FieldList(FormField(FieldOperateForm))
    orders = FieldList(FormField(FieldOperateForm))

    def query(self, query, model=None):
        query: BaseQuery
        if model is None:
            model = db.get_query_models(query)[0]

        relationship_objs = []

        filters = []
        orders = []

        def handle_operate_fields(fields, dest):
            nonlocal relationship_objs
            for form in fields:
                result = form.operator(model)
                if result is not None:
                    [operator, objs] = result
                    relationship_objs += objs
                    dest.append(operator)

        handle_operate_fields(self.filters, filters)
        handle_operate_fields(self.orders, orders)

        for relationship_model in common.list_group_by(relationship_objs):
            query = query.join(relationship_model)

        if filters:
            query = query.filter(*filters)
        if orders:
            query = query.order_by(*orders)

        return query
