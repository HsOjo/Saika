import re

from .provider import ConfigProvider


class BaseConfig:
    __disabled_keys__ = []

    def __init__(self):
        section = self.__class__.__name__.replace('Config', '')
        self._section = re.sub('[A-Z]', lambda x: '-' + x.group().lower(), section).lstrip('-')

        keys = []
        for parent_cls in self.__class__.mro()[0:-2]:
            for k, v in parent_cls.__dict__.items():
                if not k.startswith('_') and not isinstance(v, property) and not callable(v):
                    keys.append(k)

        self._keys = set(keys)
        self._provider = None

    def set_provider(self, provider):
        if self._provider is None:
            self._provider = provider  # type: ConfigProvider
            self._provider.attach(self)

    def load(self, **options):
        keys = self.keys
        for k, v in options.items():
            if k in keys:
                setattr(self, k, v)

    def refresh(self):
        if self.provider:
            options = self.provider.get(self.section)
            if options:
                self.load(**options)
        return self

    def merge(self) -> dict:
        """Merge config to flask config."""
        pass

    @property
    def section(self):
        return self._section

    @property
    def keys(self):
        return self._keys

    @property
    def data(self):
        return {k: v for k, v in self.data_all.items() if k not in self.__disabled_keys__}

    @property
    def data_all(self):
        return {k: getattr(self, k) for k in self.keys}

    @property
    def data_now(self):
        return self.refresh().data

    @property
    def provider(self):
        return self._provider
