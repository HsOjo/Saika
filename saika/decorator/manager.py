from saika import hard_code
from saika.meta_table import MetaTable


def command(f):
    commands = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_COMMANDS, [])  # type: list
    commands.append(f)
    return f
