import re
import sys
import time

import click
import termcolor
from flask import Response
from termcolor import colored
from werkzeug.serving import is_running_from_reloader

from saika import hard_code
from saika.config import Config
from saika.const import Const
from saika.context import Context
from saika.controller.cli import CliController
from saika.controller.web import WebController
from saika.decorator import *
from saika.form import AUTO
from saika.meta_table import MetaTable
from saika.socket_io import socket_io


@controller
class Saika(CliController):
    """Saika command-line interface, provided some assistant commands."""

    @doc('Document Generator', 'Generate API document JSON Data.')
    @command
    def docgen(self):
        from saika import common, Environ
        app = Environ.app

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
                        with Environ.app.test_request_context():
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

        print(docs_json)

    @doc('Config Update', 'Update(Create If Not Existed) Config File.')
    @command
    def cfgupd(self):
        Config.save()

    @doc('Run', 'Run the %s Server(Gevent based).' % Const.project_name)
    @command
    @click.option('-h', '--host', default='127.0.0.1')
    @click.option('-p', '--port', default=5000, type=int)
    @click.option('--debug', is_flag=True)
    @click.option('--use-reloader', is_flag=True)
    @click.option('--ssl-crt', default=None)
    @click.option('--ssl-key', default=None)
    def run(self, host, port, debug, use_reloader, ssl_crt, ssl_key):
        from saika import Environ
        app = Environ.app

        options = dict(debug=debug, use_reloader=use_reloader, certfile=ssl_crt, keyfile=ssl_key)
        for k, v in list(options.items()):
            if v is None:
                options.pop(k)

        if not use_reloader or is_running_from_reloader():
            print(' * Serving %s "%s"' % (app.__class__.__name__, app.import_name))
            print('   - %(project_name)s Version: %(version)s' % Const.__dict__)
            print(' * Environment: %s' % app.env)
            if app.env == 'production':
                print(termcolor.colored(
                    "   WARNING: This is a development server. "
                    "Do not use it in a production deployment.\n"
                    "   Use a production WSGI server instead.",
                    color="red")
                )
            print(' * Debug mode: %s' % ('on' if app.debug else 'off'))
            print(' * Running on http://%s:%s/ (Press CTRL+C to quit)' % (host, port))

        @app.after_request
        def print_log(resp: Response):
            req = Context.request
            color = 'yellow' if resp.status_code != 200 else 'grey'
            print('%(remote_addr)s - - [%(time)s] "%(request)s" %(status_code)s' % dict(
                remote_addr=req.remote_addr,
                time=time.strftime('%d/%b/%Y %H:%M:%S'),
                request=colored('%(method)s %(path)s %(protocol)s' % dict(
                    method=req.method,
                    path=req.path,
                    protocol=req.environ.get('SERVER_PROTOCOL'),
                ), color),
                status_code=resp.status_code,
            ), file=sys.stderr)
            return resp

        socket_io.server.eio.async_mode = 'gevent'
        try:
            socket_io.run(app, host, port, log_output=True, **options)
        except KeyboardInterrupt:
            pass
