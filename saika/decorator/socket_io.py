from saika import hard_code
from saika.meta_table import MetaTable


def on_namespace(namespace, **options):
    opts = locals().copy()
    opts.update(opts.pop('options'))

    def wrapper(cls):
        controllers = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_SIO_CONTROLLER_CLASSES, [])  # type: list
        controllers.append(cls)
        MetaTable.set(cls, hard_code.MK_OPTIONS, opts)
        return cls

    return wrapper
