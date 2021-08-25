import importlib
import os
import re
from typing import Any

import click

from saika import hard_code, common
from saika.config import Config
from saika.const import Const
from saika.controller.cli import CliController
from saika.controller.web import WebController
from saika.decorator import *
from saika.environ import Environ
from saika.form import AUTO
from saika.meta_table import MetaTable
from saika.server import *


@controller
class Saika(CliController):
    """Saika command-line interface, provided some assistant commands."""

    def callback_before_register(self):
        if not Environ.is_pyinstaller():
            command(self.make.__func__)
            command(self.lsmods.__func__)
            command(self.docgen.__func__)

    @doc('Document Generator', 'Generate API document JSON Data.')
    def docgen(self):
        app = self.app

        validate_default = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_FORM_VALIDATE)

        docs = {}
        for _controller in app.controllers:
            if not isinstance(_controller, WebController):
                continue

            _doc = MetaTable.get(_controller.__class__, hard_code.MK_DOCUMENT, dict(name=_controller.name)).copy()
            opts = _controller.options

            api_doc = {}
            for _func in _controller._functions:
                func = _func.__func__
                metas = MetaTable.all(func)

                url_prefix = opts.get(hard_code.MK_URL_PREFIX)
                rule_str = metas.get(hard_code.MK_RULE_STR)
                methods = metas.get(hard_code.MK_METHODS)

                form_cls = metas.get(hard_code.MK_FORM_CLASS)
                form_args = metas.get(hard_code.MK_FORM_ARGS)  # type: dict

                # 从所有API方法遍历，故存在部分无表单API
                form_validate = None
                if form_args is not None:
                    form_validate = form_args.get(hard_code.AK_VALIDATE)
                    if form_validate is None:
                        form_validate = validate_default

                rest, rest_args = common.rule_to_rest(rule_str)
                path = '%s%s' % (url_prefix, rest)
                for method in methods:
                    validate = form_validate
                    if form_validate == AUTO:
                        validate = method != 'GET'

                    item = MetaTable.get(func, hard_code.MK_DOCUMENT, {}).copy()
                    item.update(method=method, path=path)
                    if rest_args:
                        item.update(rest_args=rest_args)
                    if form_cls:
                        with app.test_request_context():
                            form_ = form_cls()
                        item.update(validate=validate, form=form_.dump_fields(), form_type=form_.form_type)

                    item_id = re.sub(r'[^A-Z]', '_', path.upper()).strip('_')
                    item_id = re.sub(r'_+', '_', item_id)
                    if len(methods) > 1:
                        item_id += ('_%s' % method).upper()

                    api_doc[item_id] = item

            _doc['function'] = api_doc
            docs[_controller.name] = _doc

        docs = common.obj_standard(docs, True, True, True)
        docs_json = common.to_json(docs, indent=2, sort_keys=True)

        click.echo(docs_json)

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

    @doc('Make Spec', 'Use for PyInstaller.')
    @click.option('-n', '--name')
    @click.option('-k', '--key', default=common.generate_uuid().replace('-', '')[:16])
    @click.option('-F', '--onefile', is_flag=True)
    @click.option('-b', '--build', is_flag=True)
    @click.option('-d', '--datas', nargs=2, multiple=True)
    @click.option('-h', '--hiddenimports', multiple=True)
    @click.option('-P', '--collect-py-module', multiple=True)
    @click.option('-D', '--collect-data', multiple=True)
    @click.option('-B', '--collect-binaries', multiple=True)
    @click.option('-S', '--collect-submodules', multiple=True)
    @click.option('-A', '--collect-all', multiple=True)
    @click.argument('main')
    def make(self, main: str, build: bool, collect_py_module: tuple, **opts):
        app_modules = self.app.sub_modules
        ext_modules = self.app.ext_modules
        all_modules = app_modules + ext_modules + [
            'logging.config', 'gunicorn.glogging',
        ]
        root_modules = [i for i in all_modules if '.' not in i]

        opts['collect_data'] = list(opts.get('collect_data', ())) + root_modules
        opts['hiddenimports'] = list(opts.get('hiddenimports', ())) + all_modules
        datas = opts['datas'] = list(opts.get('datas', ()))

        def add_module_data(module: Any, rel_path):
            datas.append((
                os.path.join(module.__path__[0], rel_path),
                os.path.join(module.__package__, os.path.dirname(rel_path)),
            ))

        def collect_module_py(module):
            module_name = module.__name__
            module_dir = os.path.dirname(module.__file__)

            sub_modules = common.walk_modules(module)
            sub_files = common.walk_files(module_dir, lambda d, f, p: f.endswith('.py'))
            sub_files = [f.replace(
                module_dir, module_name
            ).replace('/__init__', '').replace('.py', '').replace('/', '.') for f in sub_files]

            py_files = list(set(sub_files) - set(sub_modules))
            py_files = ['%s.py' % file.replace('.', '/').replace('%s/' % module_name, '', 1) for file in py_files]

            for py_file in py_files:
                add_module_data(module, py_file)

        collect_py_module = [*collect_py_module, 'flask_migrate']
        for name in collect_py_module:
            collect_module_py(importlib.import_module(name))

        opts.setdefault('copy_metadata', [])
        opts.setdefault('recursive_copy_metadata', [])

        try:
            from PyInstaller.building import makespec, build_main
        except ImportError:
            raise Exception('You should install PyInstaller first.')
        else:
            path_spec = makespec.main([main], **opts)

            if build:
                opts_build = {}
                opts_build.setdefault('distpath', './dist')
                opts_build.setdefault('workpath', './build')
                build_main.main(None, path_spec, True, **opts_build)

    @doc('Run', 'The Ultra %s Web Server.' % Const.project_name)
    @command
    @click.option('-h', '--host', default='127.0.0.1')
    @click.option('-p', '--port', default=5000, type=int)
    @click.option('-t', '--type', default=None, type=click.Choice([TYPE_GEVENT, TYPE_GUNICORN]))
    @click.option('-d', '--debug', is_flag=True)
    @click.option('-r', '--use-reloader', is_flag=True)
    @click.option('-c', '--ssl-crt', default=None)
    @click.option('-k', '--ssl-key', default=None)
    def run(self, host, port, type, debug, use_reloader, ssl_crt, ssl_key, **kwargs):
        if type is None:
            if self.app.env == 'production':
                type = TYPE_GUNICORN
            else:
                type = TYPE_GEVENT

        SERVER_MAPPING[type](self.app).run(
            host, port, debug, use_reloader, ssl_crt, ssl_key, **kwargs
        )
