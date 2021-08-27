import re

import click

from saika import hard_code, common
from saika.controller.web import WebController
from saika.decorator import *
from saika.environ import Environ
from saika.form import AUTO
from saika.meta_table import MetaTable


@doc('Document Generator', 'Generate API document JSON Data.')
def docgen():
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
