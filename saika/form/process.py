from saika import hard_code, common
from saika.context import Context
from saika.enums import PARAMS_MISMATCH
from saika.environ import Environ
from saika.exception import AppException
from saika.meta_table import MetaTable

AUTO = object()


class FormException(AppException):
    pass


@Environ.app.before_request
def process_form():
    if Context.request.method == 'OPTIONS':
        return

    f = Context.get_view_function()
    cls = MetaTable.get(f, hard_code.MK_FORM_CLASS)
    if cls is not None:
        args = MetaTable.get(f, hard_code.MK_FORM_ARGS)
        form = cls(**args)
        Context.g_set(hard_code.MK_FORM, form)

        validate = args.get(hard_code.AK_VALIDATE, AUTO)
        if validate is AUTO:
            validate = Context.request.method != 'GET'
        if validate and not form.validate():
            raise FormException(*PARAMS_MISMATCH, data=dict(
                errors=common.obj_standard(form.errors, True, True)
            ))
