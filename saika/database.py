from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from . import hard_code
from .config import Config
from .meta_table import MetaTable


class Database(SQLAlchemy):
    session: Session

    def dispose_engine(self, **kwargs):
        engine = self.get_engine(**kwargs)  # type: Engine
        engine.dispose()

    @staticmethod
    def query(model):
        query = getattr(model, 'query')  # type: BaseQuery
        return query

    @staticmethod
    def get_primary_key(model):
        return [column.name for column in model.__table__.primary_key]

    @property
    def models(self):
        return MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODEL_CLASSES, [])  # type: list

    def get_relationship_objs(self, field):
        primary, secondary = None, None

        if hasattr(field.comparator, 'entity'):
            primary = field.comparator.entity.class_

        if hasattr(field.prop, 'secondary'):
            models = dict((model.__tablename__, model) for model in self.models)
            secondary = field.prop.secondary
            if hasattr(secondary, 'name'):
                secondary = models.get(secondary.name)

        return primary, secondary

    def add_instance(self, instance, commit=True):
        self.session.add(instance)
        if commit:
            self.session.commit()

    def delete_instance(self, instance, commit=True):
        self.session.delete(instance)
        if commit:
            self.session.commit()


@Config.process
def merge_uri(config):
    db = Config.section(hard_code.CK_DATABASE)
    driver = db['driver'].lower()
    if 'mysql' in driver or 'postgresql' in driver:
        uri = '%(driver)s://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s?charset=%(charset)s' % db
    else:
        uri = '%(driver)s://%(path)s' % db

    config['SQLALCHEMY_DATABASE_URI'] = uri


db = Database()
migrate = Migrate()
