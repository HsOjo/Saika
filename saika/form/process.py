from wtforms_json import init

from saika import hard_code, common
from saika.context import Context
from saika.decorator.request import before_app_request
from saika.enums import PARAMS_MISMATCH
from saika.exception import AppException
from saika.meta_table import MetaTable

init()
AUTO = object()


class FormException(AppException):
    pass


@before_app_request
def process_form():
    if Context.request.method == 'OPTIONS':
        return

    f = Context.get_view_function()
    cls = MetaTable.get(f, hard_code.MK_FORM_CLASS)
    if cls is not None:
        kwargs = MetaTable.get(f, hard_code.MK_FORM_ARGS).copy()  # type: dict

        validate = kwargs.pop(hard_code.AK_VALIDATE)
        validate = AUTO if validate is None else validate

        form = cls(**kwargs)
        Context.g_set(hard_code.GK_FORM, form)

        if validate is AUTO:
            validate = Context.request.method != 'GET'
        if validate and not form.validate():
            raise FormException(*PARAMS_MISMATCH, data=dict(
                errors=common.obj_standard(form.errors, True, True)
            ))
