from saika.database import db
from .forms import FieldOperateForm


class Service:
    def __init__(self, model_class):
        self.model_class = model_class
        self.model_pks = db.get_primary_key(model_class)

        self._orders = []
        self._filters = []

        self._processes = []
        self._auto_commit = True

    def set_orders(self, *orders):
        self._orders = orders

    def set_filters(self, *filters):
        self._filters = filters

    def orders(self, *orders):
        return self.processes(lambda query: query.order_by(*orders))

    def filters(self, *filters):
        return self.processes(lambda query: query.filter(*filters))

    def processes(self, *query_processes):
        self._processes += query_processes
        return self

    def auto_commit(self, enable=True):
        self._auto_commit = enable
        return self

    @property
    def query(self):
        return db.query(self.model_class)

    @property
    def query_filter(self):
        query = self.query
        if self._filters:
            query = query.filter(*self._filters)
        return query

    @property
    def query_order(self):
        query = self.query_filter
        if self._orders:
            query = query.order_by(*self._orders)
        return query

    @property
    def pk_field(self):
        [pk] = self.model_pks
        field = getattr(self.model_class, pk)
        return field

    def pk_filter(self, *ids):
        if len(ids) == 1:
            return self.pk_field.__eq__(*ids)
        else:
            return self.pk_field.in_(ids)

    def process_query(self, query=None, clear=True):
        if query is None:
            query = self.query
        for process in self._processes:
            query = process(query) if callable(process) else process
        if clear:
            self._processes.clear()

        if self._auto_commit:
            db.session.commit()

        return query

    def list(self, page, per_page, **kwargs):
        return self.process_query(
            self.query_order
        ).paginate(page, per_page, **kwargs)

    def get_one(self):
        return self.process_query(
            self.query_filter
        ).first()

    def get_all(self):
        return self.process_query(
            self.query_order
        ).all()

    def item(self, id, **kwargs):
        return self.filters(
            self.pk_filter(id)
        ).get_one()

    def items(self, *ids, **kwargs):
        return self.filters(
            self.pk_filter(*ids)
        ).get_all()

    def add(self, **kwargs):
        model = self.model_class(**kwargs)
        db.add_instance(model)
        return model

    def edit(self, *ids, **kwargs):
        ids = self.collect_ids(ids, kwargs)
        result = self.filters(
            self.pk_filter(*ids)
        ).process_query(
            self.query_filter
        ).update(kwargs)
        if self._auto_commit:
            db.session.commit()
        return result

    def delete(self, *ids, **kwargs):
        ids = self.collect_ids(ids, kwargs)
        result = self.filters(
            self.pk_filter(*ids)
        ).process_query(
            self.query_filter
        ).delete()
        if self._auto_commit:
            db.session.commit()
        return result

    @staticmethod
    def collect_ids(ids, kwargs):
        id_ = kwargs.pop('id', None)
        if id_ is not None:
            ids = [id_, *ids]

        return ids
