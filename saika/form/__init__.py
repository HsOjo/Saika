from saika import hard_code
from saika.meta_table import MetaTable
from .field import ListField
from .forms import Form, ArgsForm
from .process import FormException


def simple_choices(obj):
    if isinstance(obj, list):
        return [(i, i) for i in obj]
    elif isinstance(obj, dict):
        return [(v, k) for k, v in obj.items()]
    return obj


def set_default_validate(enable=False):
    MetaTable.set(hard_code.MI_GLOBAL, hard_code.MK_FORM_VALIDATE, enable)
