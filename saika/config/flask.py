from saika.const import Const
from saika.decorator import config
from .free import FreeConfig


@config
class FlaskConfig(FreeConfig):
    SECRET_KEY = Const.project_name
    WTF_CSRF_ENABLED = False
