from saika.database import db
from .forms import FieldOperateForm


class Service:
    def __init__(self, model_class):
        self.model_class = model_class
        self.model_pks = db.get_primary_key(model_class)
        self.order = None

    def set_order(self, *order):
        self.order = order

    @property
    def query(self):
        return db.query(self.model_class)

    @property
    def query_order(self):
        query = self.query
        if self.order:
            query = query.order_by(*self.order)
        return query

    def list(self, page, per_page, query=None, **kwargs):
        if query is None:
            query = self.query_order
        return query.paginate(page, per_page)

    def item(self, id, query=None, **kwargs):
        if query is None:
            query = self.query
        return query.get(id)

    def add(self, **kwargs):
        model = self.model_class(**kwargs)
        db.add_instance(model)
        return model

    def edit(self, id, **kwargs):
        item = self.item(id)
        if not item:
            return False

        for k, v in kwargs.items():
            setattr(item, k, v)

        db.add_instance(item)
        return True

    def delete(self, id, **kwargs):
        item = self.item(id)
        db.delete_instance(item)

    def delete_multiple(self, ids, query=None, **kwargs):
        if query is None:
            query = self.query
        model = self.model_class
        [pk] = self.model_pks
        field = getattr(model, pk)
        result = query.filter(field.in_(ids)).delete()
        return result == len(ids)
