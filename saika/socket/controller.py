from saika.controller import ControllerBase


class SocketController(ControllerBase):
    def instance_register(self, socket):
        self.callback_before_register()
        socket.register_blueprint(self.blueprint, **self.options)
