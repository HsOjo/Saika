from sqlalchemy.engine import make_url, URL

from .database import DatabaseConfig


class FileDBConfig(DatabaseConfig):
    path = ''

    def merge(self) -> dict:
        result = super().merge()
        url = make_url('%(driver)s:///%(path)s' % self.data)  # type: URL
        url.update_query_pairs(self.query_args.items())
        result.update(
            SQLALCHEMY_DATABASE_URI=str(url)
        )
        return result
