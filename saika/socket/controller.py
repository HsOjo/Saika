from saika.controller import WebController, BaseController


class SocketController(WebController):
    def register(self, socket):
        super(BaseController).register(None)
        socket.register_blueprint(self.blueprint, **self.options)
