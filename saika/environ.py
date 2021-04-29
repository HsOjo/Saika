from flask import Flask


class Environ:
    app: Flask = None
    program_path: str
    config_path: str
    data_path: str

    @staticmethod
    def into_app_context_do(f, *args, **kwargs):
        with Environ.app.app_context():
            return f(*args, **kwargs)

    @staticmethod
    def into_request_context_do(environ, f, *args, **kwargs):
        with Environ.app.request_context(environ):
            return f(*args, **kwargs)
