import re
from typing import List

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from . import hard_code, common
from .config import Config
from .environ import Environ
from .meta_table import MetaTable


class Database(SQLAlchemy):
    session: Session

    def __init__(self, *args, **kwargs):
        engine_options = kwargs.pop('engine_options', {})
        engine_options.setdefault('json_serializer', common.to_json)
        engine_options.setdefault('json_deserializer', common.from_json)
        super().__init__(*args, **kwargs, engine_options=engine_options)

    def dispose_engine(self, **kwargs):
        engine = self.get_engine(**kwargs)  # type: Engine
        engine.dispose()

    def query(self, model):
        self.session.commit()
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

    def get_query_models(self, query):
        models = [i.get('entity') for i in query.column_descriptions]
        models = [model for model in models if model is not None]
        return models

    def add_instance(self, instance, commit=True):
        self.session.add(instance)
        if commit:
            self.session.commit()

    def delete_instance(self, instance, commit=True):
        self.session.delete(instance)
        if commit:
            self.session.commit()

    @staticmethod
    def dump_instance(instance, *columns, hidden_columns: List[str] = None):
        if not hasattr(instance, '__table__'):
            return None

        table_columns = list(instance.__table__.columns)
        table_columns_name = [column.name for column in table_columns]
        model_props = dict(instance.__class__.__dict__)
        if not columns:
            columns = table_columns

        def preprocess_columns(columns):
            if columns is None:
                return []

            result = list(columns)
            for i, column in enumerate(result):
                if isinstance(column, property):
                    for k, v in model_props.items():
                        if column is v:
                            result[i] = k
                            break
                elif column in table_columns:
                    result[i] = column.name
            return result

        columns = preprocess_columns(columns)
        hidden_columns = preprocess_columns(hidden_columns)

        def match_columns(column, target_columns):
            result = []
            if column == '*':
                result += target_columns
            else:
                for match_column in target_columns:
                    if isinstance(match_column, str):
                        if re.match(column.replace('*', '.*'), match_column):
                            result.append(match_column)

            return result

        dump_columns = []
        for column in columns:
            if isinstance(column, str) and '*' in column:
                dump_columns += match_columns(column, table_columns_name)
            else:
                dump_columns.append(column)

        dump_columns = common.list_group_by(dump_columns)

        if hidden_columns is not None:
            for column in hidden_columns:
                if column in dump_columns:
                    dump_columns.remove(column)
                elif isinstance(column, str) and '*' in column:
                    for column_match in match_columns(column, dump_columns):
                        dump_columns.remove(column_match)

        if dump_columns:
            data = {}
            for column in dump_columns:
                if callable(column):
                    patch = column(instance)  # type: dict
                    data.update(patch)
                elif isinstance(column, str):
                    data[column] = getattr(instance, column)
                else:
                    raise Exception('Invalid Column:', column)

            return data

    @staticmethod
    def load_instance(instance, **kwargs):
        if not hasattr(instance, '__table__'):
            return False

        table_columns = list(instance.__table__.columns)
        table_columns_name = [column.name for column in table_columns]
        for k, v in kwargs:
            if k in table_columns_name:
                setattr(instance, k, v)

        return True


@Config.process
def merge_uri(config):
    db = Config.section(hard_code.CK_DATABASE)
    if not db:
        Environ.app.logger.warning(' * Database config is not defined.')
        return

    driver = db['driver'].lower()
    if 'mysql' in driver or 'postgresql' in driver:
        uri = '%(driver)s://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s?charset=%(charset)s' % db
    else:
        uri = '%(driver)s://%(path)s' % db

    config['SQLALCHEMY_DATABASE_URI'] = uri


db = Database()
migrate = Migrate()
