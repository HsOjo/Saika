from saika import BaseConfig


class DatabaseConfig(BaseConfig):
    driver = 'sqlite'

    query_args = {}

    echo_sql = False
    track_modifications = False

    def merge(self) -> dict:
        return dict(
            SQLALCHEMY_ECHO=self.echo_sql,
            SQLALCHEMY_TRACK_MODIFICATIONS=self.track_modifications,
        )
