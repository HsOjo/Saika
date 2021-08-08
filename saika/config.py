import json
import os

from . import hard_code, common
from .environ import Environ

_config = {}
_processes = []
_config_mtime = 0


def check_and_reload(f):
    def wrapper(*args, **kwargs):
        if os.path.exists(Environ.config_path):
            global _config_mtime
            mtime = os.path.getmtime(Environ.config_path)
            if _config_mtime != mtime:
                Config.load()
                _config_mtime = mtime
        return f(*args, **kwargs)

    return wrapper


class Config:
    @staticmethod
    def load():
        global _config
        path = Environ.config_path
        if not os.path.exists(path):
            _config = {}
            Environ.app.logger.warning(' * Config not exist: %s' % path)
        else:
            with open(path, 'r') as io:
                _config = json.load(io)

    @staticmethod
    def save(path):
        cfg_str = common.to_json(_config, indent=2)
        with open(path, 'w') as io:
            io.write(cfg_str)

    @staticmethod
    @check_and_reload
    def section(key):
        cfg = _config.get(key, {})  # type: dict
        return cfg

    @staticmethod
    @check_and_reload
    def all():
        return _config

    @staticmethod
    @check_and_reload
    def merge():
        config = {}

        for process in _processes:
            process(config)

        config.update(_config.get(hard_code.CK_CORE, {}))
        return config

    @staticmethod
    def process(f):
        _processes.append(f)
        return f
