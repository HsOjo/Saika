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

    def _process_query(self, query=None, *processes):
        if query is None:
            query = self.query

        for process in processes:
            if callable(process):
                query = process(query)
            else:
                query = process

        return query

    def list(self, page, per_page, query_processes=(), **kwargs):
        return self._process_query(
            self.query_order, *query_processes
        ).paginate(page, per_page)

    def item(self, id, query_processes=(), **kwargs):
        return self._process_query(
            self.query_filter, *query_processes,
            lambda query: query.filter(self.pk_filter(id))
        ).first()

    def add(self, **kwargs):
        model = self.model_class(**kwargs)
        db.add_instance(model)
        return model

    def edit(self, *ids, query_processes=(), **kwargs):
        return self._process_query(
            self.query_filter, *query_processes,
            lambda query: query.filter(self.pk_filter(*ids))
        ).update(kwargs)

    def delete(self, *ids, query_processes=(), **kwargs):
        if not ids:
            return 0

        return self._process_query(
            self.query_filter, *query_processes,
            lambda query: query.filter(self.pk_filter(*ids))
        ).delete()
