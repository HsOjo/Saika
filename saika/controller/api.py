import sys
import traceback

from flask import jsonify

from saika.exception import AppException, APIException
from .web import WebController
from .. import hard_code


class APIController(WebController):
    def callback_before_register(self):
        @self.blueprint.errorhandler(AppException)
        def convert(e: AppException):
            return APIException(e.error_code, e.msg, e.data)

        @self.blueprint.errorhandler(Exception)
        def catch(e: Exception):
            traceback.print_exc(file=sys.stderr)
            [exc_str] = list(traceback.TracebackException(*sys.exc_info()).format_exception_only())
            return APIException(data=dict(exc=exc_str))

    def _record_response(self, code, msg):
        self.context.g_set(hard_code.GK_RESPONSE_CODE, code)
        self.context.g_set(hard_code.GK_RESPONSE_MSG, msg)

    def response(self, code=0, msg=None, **data):
        self._record_response(code, msg)
        return jsonify(code=code, msg=msg, data=data)

    def success(self, code=0, msg=None, **data):
        self._record_response(code, msg)
        raise APIException(code, msg, data)

    def error(self, code=1, msg=None, **data):
        self._record_response(code, msg)
        raise APIException(code, msg, data)
