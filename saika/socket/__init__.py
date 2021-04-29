from flask_sockets import Sockets
from flask_uwsgi_websocket import GeventWebSocket

from .controller import SocketController
from .event import EventSocketController

try:
    import uwsgi

    socket = GeventWebSocket()
except ImportError:
    socket = Sockets()
