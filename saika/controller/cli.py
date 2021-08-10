from saika import hard_code
from saika.meta_table import MetaTable
from .blueprint import BlueprintController


class CliController(BlueprintController):
    def __init__(self):
        super().__init__()
        self._blueprint.name = self._blueprint.name.replace('_', '-')
        self._blueprint.cli.help = self.__class__.__doc__

    def _register_functions(self):
        functions = self.get_functions(CliController)
        commands = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_COMMANDS, [])  # type: list

        for f in functions:
            _f = f
            if hasattr(f, '__func__'):
                f = f.__func__

            if f in commands:
                self._blueprint.cli.command()(_f)
                self._functions.append(_f)