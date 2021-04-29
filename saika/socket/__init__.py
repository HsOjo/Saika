from flask_sockets import Sockets

from .controller import SocketController
from .event import EventSocketController

socket = Sockets()
