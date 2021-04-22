from saika import hard_code
from saika.meta_table import MetaTable


def form(form_cls, validate=None, **kwargs):
    if validate is None:
        validate = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_FORM_VALIDATE, False)

    kwargs['validate'] = validate

    def wrapper(f):
        MetaTable.set(f, hard_code.MK_FORM_CLASS, form_cls)
        MetaTable.set(f, hard_code.MK_FORM_ARGS, kwargs)
        return f

    return wrapper
