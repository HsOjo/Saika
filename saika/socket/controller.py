from saika.controller import WebController, BaseController


class SocketController(WebController):
    def register(self, socket):
        BaseController.register(self)
        socket.register_blueprint(self.blueprint, **self.options)
