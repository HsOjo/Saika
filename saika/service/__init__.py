from saika.database import db
from .forms import FieldOperateForm


class Service:
    def __init__(self, model_class):
        self.model_class = model_class
        self.model_pks = db.get_primary_key(model_class)
        self.order = None
        self.filter = None

    def set_order(self, *order):
        self.order = order

    def set_filter(self, *filter):
        self.filter = filter

    @property
    def query(self):
        return db.query(self.model_class)

    @property
    def query_filter(self):
        query = self.query
        if self.filter:
            query = query.filter(*self.filter)
        return query

    @property
    def query_order(self):
        query = self.query_filter
        if self.order:
            query = query.order_by(*self.order)
        return query

    def list(self, page, per_page, query=None, **kwargs):
        if query is None:
            query = self.query_order
        return query.paginate(page, per_page)

    def item(self, id, query=None, **kwargs):
        if query is None:
            query = self.query_filter
        [pk] = self.model_pks
        field = getattr(self.model_class, pk)
        item = query.filter(field.__eq__(id)).first()
        return item

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
        return self.delete_multiple([id], **kwargs)

    def delete_multiple(self, ids, query=None, **kwargs):
        if not ids:
            return

        if query is None:
            query = self.query_filter
        [pk] = self.model_pks
        field = getattr(self.model_class, pk)
        result = query.filter(field.in_(ids)).delete()
        db.session.commit()
        return result
