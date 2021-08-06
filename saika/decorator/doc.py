from saika import hard_code
from saika.meta_table import MetaTable


def doc(name, description=None, **kwargs):
    def wrapper(obj):
        MetaTable.set(
            obj, hard_code.MK_DOCUMENT,
            dict(name=name, description=description, **kwargs)
        )

        if not obj.__doc__:
            obj.__doc__ = '%s: %s' % (name, description) if description else name

        return obj

    return wrapper
