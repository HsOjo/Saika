from .gevent import Gevent
from .gunicorn import Gunicorn

TYPE_GEVENT = 'gevent'
TYPE_GUNICORN = 'gunicorn'

SERVER_MAPPING = {
    TYPE_GEVENT: Gevent,
    TYPE_GUNICORN: Gunicorn,
}
