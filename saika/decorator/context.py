from functools import wraps

from saika.environ import Environ


def with_app_context(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with Environ.app.app_context():
            return f(*args, **kwargs)

    return wrapper
