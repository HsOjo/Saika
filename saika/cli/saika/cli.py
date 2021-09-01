import click

from saika.config import Config
from saika.const import Const
from saika.controller.cli import CliController
from saika.decorator import *
from saika.environ import Environ
from saika.server import *
from .docgen import docgen
from .make import make


@controller
class Saika(CliController):
    """Saika command-line interface, provided some assistant commands."""

    def callback_before_register(self):
        if not Environ.is_pyinstaller():
            self.bind_command(self.lsmods)
            self.bind_command(make)
            self.bind_command(docgen)

    @doc('Config Update', 'Update(Create If Not Existed) Config File.')
    @command
    def cfgupd(self):
        Config.save()
        click.echo('Update Finished.')

    @doc('List Modules', 'Use for Packing...(Such as PyInstaller).')
    @click.option('-a', '--all', is_flag=True)
    def lsmods(self, all: bool):
        modules = self.app.sub_modules
        if all:
            modules += self.app.ext_modules

        click.echo('\n'.join(modules))

    @doc('Run', 'The Ultra %s Web Server.' % Const.project_name)
    @command
    @click.option('-h', '--host', default='127.0.0.1')
    @click.option('-p', '--port', default=5000, type=int)
    @click.option('-t', '--type', default=None, type=click.Choice([TYPE_GEVENT, TYPE_GUNICORN]))
    @click.option('-d', '--debug', is_flag=True)
    @click.option('-r', '--use-reloader', is_flag=True)
    @click.option('-c', '--ssl-crt', default=None)
    @click.option('-k', '--ssl-key', default=None)
    @click.option('-o', '--option', type=(str, str), multiple=True)
    def run(self, host, port, type, debug, use_reloader, ssl_crt, ssl_key, **kwargs):
        if type is None:
            if self.app.env == 'production':
                type = TYPE_GUNICORN
            else:
                type = TYPE_GEVENT

        for k, v in kwargs['option']:
            kwargs[k] = v
        kwargs.pop('option')

        SERVER_MAPPING[type](self.app).run(
            host, port, debug, use_reloader, ssl_crt, ssl_key, **kwargs
        )
