from sqlalchemy.engine import make_url, URL

from saika.const import Const
from .database import DatabaseConfig


class ConnectDBConfig(DatabaseConfig):
    user = '[user]'
    password = '[password]'
    host = 'localhost'
    port = 3306
    database = '[database]'

    def merge(self) -> dict:
        result = super().merge()
        url = make_url('%(driver)s://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % self.data)  # type: URL
        url.update_query_pairs(self.query_args.items())
        result.update(
            SQLALCHEMY_DATABASE_URI=str(url)
        )
        return result
