from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from . import hard_code
from .config import Config


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
