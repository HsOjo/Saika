import re

from flask import render_template

from saika import hard_code
from saika.meta_table import MetaTable
from .web import WebController


class ViewController(WebController):
    def assign(self, **kwargs):
        view_context = self.context.g_get(hard_code.GK_VIEW_CONTEXT)
        if view_context is None:
            view_context = {}
            self.context.g_set(hard_code.GK_VIEW_CONTEXT, view_context)
        view_context.update(kwargs)

    def fetch(self, template=None):
        if template is None:
            view_function = self.context.get_view_function()

            url_prefix = self.options.get(hard_code.MK_URL_PREFIX).strip('/')  # type: str
            rule_str = MetaTable.get(view_function, hard_code.MK_RULE_STR).strip('/')  # type: str

            if not url_prefix:
                url_prefix = self.name
            if not rule_str:
                rule_str = view_function.__name__

            template = '%s/%s' % (url_prefix, rule_str)
            template = re.sub('<.+?>', '', template)
            template = re.sub('/+', '/', template)
            template = '%s.html' % template.strip('/')

        view_context = self.context.g_get(hard_code.GK_VIEW_CONTEXT, {})
        return render_template(template, **view_context)
