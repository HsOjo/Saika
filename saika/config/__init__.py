from typing import List, Dict

from saika.environ import Environ
from .base import BaseConfig
from .flask import FlaskConfig
from .free import FreeConfig
from .provider import *


class Config:
    @staticmethod
    def all(to_dict=False):
        result = list(Environ.app.configs.values())  # type: List[BaseConfig]
        if to_dict:
            result = {cfg.section: cfg for cfg in result}  # type: Dict[str, BaseConfig]

        return result

    @staticmethod
    def get(config_cls):
        config = Environ.app.configs[config_cls]  # type: BaseConfig
        return config.refresh()

    @staticmethod
    def save(*configs):
        if not configs:
            configs = Config.all()

        providers = set([config.provider for config in configs])
        for provider in providers:
            provider: ConfigProvider
            provider.save()
