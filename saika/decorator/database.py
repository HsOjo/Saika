from saika import hard_code
from saika.meta_table import MetaTable


def model(cls):
    models = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODEL_CLASSES, [])  # type: list
    models.append(cls)
    return cls
