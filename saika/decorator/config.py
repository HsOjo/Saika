from saika import hard_code
from saika.meta_table import MetaTable


def config(provider=None):
    def wrapper(cls):
        nonlocal provider
        if cls is provider:
            provider = None

        configs = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_CONFIG_CLASSES, [])  # type: list
        configs.append(cls)
        MetaTable.set(cls, hard_code.MK_CONFIG_PROVIDER, provider)
        return cls

    if type(provider) is type:
        return wrapper(provider)

    return wrapper
