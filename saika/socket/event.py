import json

from flask_uwsgi_websocket import WebSocketClient
from geventwebsocket import WebSocketError
from geventwebsocket.websocket import WebSocket, MSG_SOCKET_DEAD

from saika import hard_code, common
from saika.environ import Environ
from .controller import SocketController


class EventSocketController(SocketController):
    def handle(self, socket):
        if isinstance(socket, WebSocketClient):
            Environ.into_request_context_do(socket.environ, self._handle, socket)
        elif isinstance(socket, WebSocket):
            self._handle(socket)

    def _handle(self, socket):
        self.context.g_set(hard_code.GK_SOCKET, socket)
        self.on_connect()
        while self._loop:
            data_str = None
            try:
                data_str = socket.receive()
                if not data_str:
                    continue
                data = json.loads(data_str)  # type: dict
                if isinstance(data, dict):
                    event = 'on_%s' % data.pop('event')
                    if hasattr(self, event) and event not in dir(EventSocketController):
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
    def _loop(self):
        socket = self.socket
        if isinstance(socket, WebSocket):
            return not socket.closed
        elif isinstance(socket, WebSocketClient):
            return socket.connected
        return False

    @property
    def socket(self):
        socket = self.context.g_get(hard_code.GK_SOCKET)  # type: WebSocket
        return socket

    def send(self, data: dict):
        self.socket.send(json.dumps(common.obj_standard(data, True, True)))

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
