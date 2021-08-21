from saika import BaseConfig


class DatabaseConfig(BaseConfig):
    driver = 'sqlite'
    query_args = {}

    echo_sql = False

    pool_size = 5
    pool_timeout = 10

    track_modifications = False

    def merge(self) -> dict:
        return dict(
            SQLALCHEMY_ECHO=self.echo_sql,
            SQLALCHEMY_POOL_SIZE=self.pool_size,
            SQLALCHEMY_POOL_TIMEOUT=self.pool_timeout,
            SQLALCHEMY_TRACK_MODIFICATIONS=self.track_modifications,
        )
