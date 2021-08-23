from saika.controller import WebController, BaseController


class SocketController(WebController):
    def register(self, socket):
        BaseController.register(self)
        self._register_functions()
        socket.register_blueprint(self.blueprint, **self.options)
