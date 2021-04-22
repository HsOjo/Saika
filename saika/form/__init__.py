from .field import ListField
from .forms import Form, ArgsForm
from .process import FormException


def simple_choices(obj):
    if isinstance(obj, list):
        return [(i, i) for i in obj]
    elif isinstance(obj, dict):
        return [(v, k) for k, v in obj.items()]
    return obj
