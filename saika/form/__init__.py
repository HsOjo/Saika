from .forms import Form, ArgsForm, JSONForm, ViewArgsForm
from .process import FormException, AUTO


def simple_choices(obj):
    if isinstance(obj, list):
        return [(i, i) for i in obj]
    elif isinstance(obj, dict):
        return [(v, k) for k, v in obj.items()]
    return obj


def set_form_validate_default(enable=AUTO):
    from saika import hard_code
    from saika.meta_table import MetaTable
    MetaTable.set(hard_code.MI_GLOBAL, hard_code.MK_FORM_VALIDATE, enable)
