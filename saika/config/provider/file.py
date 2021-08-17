import os
from threading import Lock

from saika import common
from .provider import ConfigProvider


class FileProvider(ConfigProvider):
    def __init__(self, path):
        super().__init__()
        self._path = path

        self._mtime = None
        self._time_lock = Lock()

        self._data = {}
        self._data_lock = Lock()

    def check_time_reload(self):
        with self._time_lock:
            mtime = os.path.getmtime(self._path)
            if mtime != self._mtime:
                self._mtime = mtime
                self.load()

    def get(self, section) -> dict:
        self.check_time_reload()
        return super().get(section)

    def load(self):
        with self._data_lock:
            with open(self._path, 'r', encoding='utf-8') as io:
                self._data = common.from_json(io.read())

    def save(self):
        with self._data_lock:
            data_str = common.to_json(self.data, indent=2)
            with open(self._path, 'w', encoding='utf-8') as io:
                io.write(data_str)
