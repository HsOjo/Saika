import re

from flask import render_template

from saika import hard_code
from .controller import Controller


class ViewControlller(Controller):
    def assign(self, **kwargs):
        context = self.context.g_get(hard_code.GK_CONTEXT)
        if context is None:
            context = {}
            self.context.g_set(hard_code.GK_CONTEXT, context)
        context.update(kwargs)

    def fetch(self, template=None):
        if template is None:
            url_prefix = self.options.get('url_prefix')
            view_function = self.context.get_view_function()
            template = '%s/%s' % (url_prefix, view_function.__name__)
            template = re.sub('<.+?>', '', template)
            template = re.sub('/+', '/', template)
            template = '%s.html' % template.strip('/')

        context = self.context.g_get(hard_code.GK_CONTEXT, {})
        return render_template(template, **context)
