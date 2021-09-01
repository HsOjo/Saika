from saika.database import db
from .forms import FieldOperateForm


class Service:
    def __init__(self, model_class):
        self.model_class = model_class
        self.model_pks = db.get_primary_key(model_class)

        self.orders = None
        self.filters = None

    def set_orders(self, *orders):
        self.orders = orders

    def set_filters(self, *filters):
        self.filters = filters

    @property
    def query(self):
        return db.query(self.model_class)

    @property
    def query_filter(self):
        query = self.query
        if self.filters:
            query = query.filter(*self.filters)
        return query

    @property
    def query_order(self):
        query = self.query_filter
        if self.orders:
            query = query.order_by(*self.orders)
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
        db.session.commit()
        return self._process_query(
            self.query_order, *query_processes
        ).paginate(page, per_page)

    def get_one(self, *filters, query_processes=(), **kwargs):
        db.session.commit()
        return self._process_query(
            self.query_filter, *query_processes,
            lambda query: query.filter(*filters)
        ).first()

    def get_all(self, *filters, query_processes=(), **kwargs):
        db.session.commit()
        return self._process_query(
            self.query_order, *query_processes,
            lambda query: query.filter(*filters)
        ).all()

    def item(self, id, query_processes=(), **kwargs):
        return self.get_one(self.pk_filter(id), query_processes=query_processes, **kwargs)

    def items(self, *ids, query_processes=(), **kwargs):
        return self.get_all(self.pk_filter(*ids), query_processes=query_processes, **kwargs)

    def add(self, **kwargs):
        model = self.model_class(**kwargs)
        db.add_instance(model)
        return model

    def edit(self, id, *ids, query_processes=(), **kwargs):
        result = self._process_query(
            self.query_filter, *query_processes,
            lambda query: query.filter(self.pk_filter(id, *ids))
        ).update(kwargs)
        db.session.commit()
        return result

    def delete(self, id, *ids, query_processes=(), **kwargs):
        result = self._process_query(
            self.query_filter, *query_processes,
            lambda query: query.filter(self.pk_filter(id, *ids))
        ).delete()
        db.session.commit()
        return result
