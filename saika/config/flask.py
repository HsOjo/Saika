from saika import common
from saika.decorator import config
from .free import FreeConfig


@config
class FlaskConfig(FreeConfig):
    SECRET_KEY = common.generate_uuid()
    WTF_CSRF_ENABLED = False
