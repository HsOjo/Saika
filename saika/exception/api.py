from saika import common
from .exception import AppException


class APIException(AppException):
    def __init__(self, *args, **kwargs):
        kwargs['code'] = 200
        super().__init__(*args, **kwargs)

    def get_body(self, environ=None):
        return common.to_json(
            common.obj_standard(dict(
                code=self.error_code,
                msg=self.msg,
                data=self.data,
            ), True, True))
