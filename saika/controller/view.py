import re

from flask import render_template

from saika import hard_code
from saika.meta_table import MetaTable
from .web import WebController


class ViewControlller(WebController):
    def assign(self, **kwargs):
        context = self.context.g_get(hard_code.GK_CONTEXT)
        if context is None:
            context = {}
            self.context.g_set(hard_code.GK_CONTEXT, context)
        context.update(kwargs)

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

        context = self.context.g_get(hard_code.GK_CONTEXT, {})
        return render_template(template, **context)
