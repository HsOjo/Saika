import json

from . import hard_code

_config = {}
_processes = []


class Config:
    @staticmethod
    def load(path):
        global _config
        with open(path, 'r') as io:
            _config = json.load(io)

    @staticmethod
    def save(path):
        cfg_str = json.dumps(_config, ensure_ascii=False, indent=2)
        with open(path, 'w') as io:
            io.write(cfg_str)

    @staticmethod
    def section(key):
        cfg = _config.get(key)  # type: dict
        return cfg

    @staticmethod
    def all():
        return _config

    @staticmethod
    def merge():
        config = {}

        for process in _processes:
            process(config)

        config.update(_config.get(hard_code.CK_CORE))
        return config

    @staticmethod
    def process(f):
        _processes.append(f)
        return f
