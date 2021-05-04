from saika import hard_code
from saika.environ import Environ
from saika.meta_table import MetaTable


def rule(rule_str: str):
    def wrapper(f):
        MetaTable.set(f, hard_code.MK_RULE_STR, rule_str)
        return f

    return wrapper


def rule_rs(rule_str: str):
    def wrapper(f):
        MetaTable.set(f, hard_code.MK_RULE_STR, rule_str.rstrip('/'))
        return f

    return wrapper


def controller(url_prefix=None, template_folder=None, static_folder=None, **options):
    opts = locals().copy()
    opts.update(opts.pop('options'))

    def wrapper(cls):
        nonlocal url_prefix
        if url_prefix is None:
            module = cls.__module__  # type: str
            module = module.lstrip(Environ.app.__module__)
            opts['url_prefix'] = module.replace('.', '/')

        controllers = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_CONTROLLER_CLASSES, [])  # type: list
        controllers.append(cls)
        MetaTable.set(cls, hard_code.MK_OPTIONS, opts)
        return cls

    return wrapper


def _method(f, method):
    methods = MetaTable.get(f, hard_code.MK_METHODS, [])  # type: list
    methods.append(method)
    return f


get = lambda f: _method(f, 'GET')
post = lambda f: _method(f, 'POST')
