from saika import hard_code
from saika.decorator import command
from saika.meta_table import MetaTable
from .blueprint import BlueprintController


class CliController(BlueprintController):
    def __init__(self):
        super().__init__()
        self._blueprint.name = self._blueprint.name.replace('_', '-')
        self._blueprint.cli.help = self.__class__.__doc__

    def _register_functions(self):
        commands = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_COMMANDS, [])  # type: list

        for f in self.methods:
            _f = f
            f = getattr(f, '__func__', f)

            if f in commands:
                self._blueprint.cli.command()(_f)
                self._functions.append(_f)

    def bind_command(self, cmd):
        cmd = getattr(cmd, '__func__', cmd)
        cls = self.__class__
        cmd_name = cmd.__name__
        if not hasattr(cls, cmd_name):
            setattr(cls, cmd_name, None)  # dummy attribute.
            setattr(self, cmd_name, cmd)
        command(cmd)
