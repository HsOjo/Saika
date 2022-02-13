import json

from geventwebsocket.exceptions import WebSocketError
from geventwebsocket.websocket import WebSocket, MSG_SOCKET_DEAD

from saika import hard_code, common
from .controller import SocketController


class EventSocketController(SocketController):
    @property
    def _loop(self):
        socket = self.socket
        if isinstance(socket, WebSocket):
            return not socket.closed

    def handle(self, socket: WebSocket):
        self.context.g_set(hard_code.GK_SOCKET, socket)

        self.on_connect()
        while self._loop:
            data_str = None
            try:
                data_str = socket.receive()
                if not data_str:
                    continue
                data = common.from_json(data_str)  # type: dict
                if isinstance(data, dict):
                    event = 'on_%s' % data.pop('event')
                    if event in self.attrs:
                        kwargs = data.pop('data', {})
                        getattr(self, event)(**kwargs)
                        continue
                self.on_message(data)
            except json.JSONDecodeError:
                self.on_message(data_str)
            except WebSocketError as e:
                if MSG_SOCKET_DEAD in e.args:
                    break
                self.on_error(e)
            except Exception as e:
                self.on_error(e)
        self.on_disconnect()

    @property
    def socket(self):
        socket = self.context.g_get(hard_code.GK_SOCKET)  # type: WebSocket
        return socket

    def send(self, data: dict):
        self.socket.send(common.to_json(common.obj_standard(data, True, True)))

    def emit(self, event: str, data: dict):
        self.send(dict(event=event, data=data))

    def disconnect(self, *args, **kwargs):
        self.socket.close(*args, **kwargs)

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_message(self, data):
        pass

    def on_error(self, e: Exception):
        raise e
