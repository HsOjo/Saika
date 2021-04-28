from flask_sockets import Sockets

from saika.controller import Controller


class SocketController(Controller):
    def register(self, sockets: Sockets):
        sockets.register_blueprint(self.blueprint)
