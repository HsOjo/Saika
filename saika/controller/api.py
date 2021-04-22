import sys
import traceback

from flask import jsonify

from saika.exception import AppException, APIException
from .controller import Controller


class APIController(Controller):
    def callback_before_register(self):
        @self.blueprint.errorhandler(AppException)
        def convert(e: AppException):
            return APIException(e.error_code, e.msg, e.data)

        @self.blueprint.errorhandler(Exception)
        def catch(e: Exception):
            traceback.print_exc(file=sys.stderr)
            return APIException(msg=str(e))

    def response(self, code=0, msg=None, **data):
        return jsonify(code=code, msg=msg, data=data)

    def success(self, code=0, msg=None, **data):
        raise APIException(code, msg, data)

    def error(self, code=1, msg=None, **data):
        raise APIException(code, msg, data)
