from saika.database import db
from .forms import FieldOperateForm


class Service:
    def __init__(self, model_class):
        self.model_class = model_class

    @property
    def query(self):
        return db.query(self.model_class)

    def list(self, page, per_page, query=None, **kwargs):
        if query is None:
            query = self.query
        return query.paginate(page, per_page)

    def item(self, id, query=None, **kwargs):
        if query is None:
            query = self.query
        return query.get(id)

    def add(self, **kwargs):
        model = self.model_class(**kwargs)
        db.add_instance(model)

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

    def delete_multiple(self, ids, **kwargs):
        [pk] = db.get_primary_key()
        field = getattr(self.model_class, pk)
        result = self.query.filter(field.in_(ids)).delete()
        return result == len(ids)
