from saika import hard_code
from saika.meta_table import MetaTable


def _callback(f, key):
    callbacks = MetaTable.get(hard_code.MI_CALLBACK, key, [])  # type: list
    callbacks.append(f)
    return f


before_app_request = lambda f: _callback(f, hard_code.MK_BEFORE_APP_REQUEST)
before_app_first_request = lambda f: _callback(f, hard_code.MK_BEFORE_APP_FIRST_REQUEST)
after_app_request = lambda f: _callback(f, hard_code.MK_AFTER_APP_REQUEST)
