from flask_sockets import Sockets

from saika.controller import ControllerBase


class SocketController(ControllerBase):
    def register(self, sockets: Sockets):
        self.callback_before_register()
        sockets.register_blueprint(self.blueprint, **self.options)
