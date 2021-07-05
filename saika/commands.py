import json
import re

from . import hard_code, common
from .app import SaikaApp
from .context import Context
from .form import AUTO
from .meta_table import MetaTable


def register(manager):
    def docgen():
        app = Context.current_app  # type: SaikaApp

        validate_default = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_FORM_VALIDATE)

        docs = {}
        for controller in app.web_controllers:
            doc = MetaTable.get(controller.__class__, hard_code.MK_DOCUMENT, dict(name=controller.name)).copy()
            opts = controller.options

            api_doc = {}
            for func in controller.view_functions:
                metas = MetaTable.all(func)

                url_prefix = opts.get(hard_code.MK_URL_PREFIX)
                rule_str = metas.get(hard_code.MK_RULE_STR)
                methods = metas.get(hard_code.MK_METHODS)

                form_cls = metas.get(hard_code.MK_FORM_CLASS)
                form_args = metas.get(hard_code.MK_FORM_ARGS)  # type: dict
                form_validate = None
                if form_args:
                    form_validate = form_args.get(hard_code.AK_VALIDATE, validate_default)

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
                        form = form_cls()
                        item.update(validate=validate, form=form.dump_fields(), form_type=form.type)

                    item_id = re.sub(r'[^A-Z]', '_', path.upper()).strip('_')
                    item_id = re.sub(r'_+', '_', item_id)
                    if len(methods) > 1:
                        item_id += ('_%s' % method).upper()

                    api_doc[item_id] = item

            doc['function'] = api_doc
            docs[controller.name] = doc

        docs = common.obj_standard(docs, True, True, True)
        docs_json = json.dumps(docs, indent=2, ensure_ascii=False)

        print(docs_json)

    docgen.__doc__ = 'Generate API document JSON Data.'
    manager.command(docgen)
