from saika import hard_code
from saika.meta_table import MetaTable


def form(form_cls, validate=None, **kwargs):
    kwargs[hard_code.AK_VALIDATE] = validate

    def wrapper(f):
        MetaTable.set(f, hard_code.MK_FORM_CLASS, form_cls)
        MetaTable.set(f, hard_code.MK_FORM_ARGS, kwargs)
        return f

    return wrapper
