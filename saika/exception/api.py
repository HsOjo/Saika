import json

from .exception import AppException


class APIException(AppException):
    def __init__(self, *args, **kwargs):
        kwargs['code'] = 200
        super().__init__(*args, **kwargs)

    def get_body(self, environ=None):
        try:
            return json.dumps(dict(
                code=self.error_code,
                msg=self.msg,
                data=self.data,
            ))
        except TypeError:
            return json.dumps(dict(
                code=self.error_code,
                msg=self.msg,
                data='%a' % self.data,
            ))
