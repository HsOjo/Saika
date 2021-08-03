from saika.controller import WebController


class SocketController(WebController):
    def instance_register(self, socket):
        socket.register_blueprint(self.blueprint, **self.options)
