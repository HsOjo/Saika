from .config import Config


class FreeConfig(Config):
    def load(self, **options):
        for k, v in options.items():
            setattr(self, k, v)

    @property
    def keys(self):
        keys = [*self.__class__.__dict__.keys(), *self.__dict__.keys()]
        return [k for k in set(keys) if k[0] != '_']

    def merge(self) -> dict:
        return self.data
