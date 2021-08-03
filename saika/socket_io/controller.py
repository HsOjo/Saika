import re

from flask_socketio import Namespace

from saika import hard_code
from saika.context import Context
from saika.meta_table import MetaTable


class SocketIOController(Namespace):
    def __init__(self):
        super().__init__(namespace=self.options.pop(hard_code.MK_URL_PREFIX, None))

    def instance_register(self, socket_io):
        socket_io.on_namespace(self)

    def trigger_event(self, event, *args):
        event = re.sub('[A-Z]+', lambda x: '_%s' % x.group().lower(), event)
        event = re.sub('[^a-z0-9$]', '_', event)
        event = event.strip('_')
        super().trigger_event(event, *args)

    @property
    def options(self):
        options = MetaTable.get(self.__class__, hard_code.MK_OPTIONS, {})  # type: dict
        return options

    @property
    def context(self):
        return Context

    @property
    def sid(self):
        return Context.request.sid

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def emit(self, event, data=None, broadcast=False, room=None, **kwargs):
        if broadcast:
            room = None
        elif room is None:
            room = self.sid

        return super().emit(event, data, room, **kwargs)

    def send(self, data=None, broadcast=False, room=None, **kwargs):
        if broadcast:
            room = None
        elif room is None:
            room = self.sid

        return super().send(data, room, **kwargs)

    def disconnect(self, **kwargs):
        self._inject_kwargs(kwargs)
        return super().disconnect(**kwargs)

    def rooms(self, **kwargs):
        self._inject_kwargs(kwargs)
        return super().rooms(**kwargs)

    def enter_room(self, room, **kwargs):
        self._inject_kwargs(kwargs)
        return super().enter_room(room=room, **kwargs)

    def leave_room(self, room, **kwargs):
        self._inject_kwargs(kwargs)
        return super().leave_room(room=room, **kwargs)

    def _inject_kwargs(self, kwargs: dict):
        kwargs['sid'] = kwargs.get('sid')
        if not kwargs['sid']:
            kwargs['sid'] = self.sid
        kwargs['namespace'] = kwargs.get('namespace', self.namespace)
