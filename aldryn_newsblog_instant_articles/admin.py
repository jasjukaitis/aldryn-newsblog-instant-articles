from django.conf import settings
from django.conf.urls import url, patterns
from django.contrib import admin, messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

import facebook

from aldryn_newsblog.admin import ArticleAdmin
from aldryn_newsblog.models import Article


class InstantArticleAdmin(ArticleAdmin):
    publish_template = 'admin/instant_article_publish_confirmation.html'

    def get_urls(self):
        urls = super(InstantArticleAdmin, self).get_urls()
        custom = patterns(
            '',
            url(r'^(?P<pk>[^/.]+)/instant_article/$',
                self.admin_site.admin_view(self.instant_article),
                name='aldryn_newsblog_article_publish_instant_article'),
        )
        return custom + urls

    def instant_article(self, request, pk):
        obj = self.get_object(request, pk)
        if request.method == 'POST':
            request.toolbar.edit_mode = False
            html = render_to_string(
                'aldryn_newsblog_instant_articles/instant_article.html',
                context={
                    'article': obj,
                    'base_url': 'https://%s' % get_current_site(request)
                },
                context_instance=RequestContext(request))
            graph = facebook.GraphAPI(
                access_token=settings.FACEBOOK_ACCESS_TOKEN, version='2.6')
            graph.extend_access_token(
                app_id=settings.FACEBOOK_APP_ID,
                app_secret=settings.FACEBOOK_APP_SECRET)
            article = graph.put_object(
                parent_object=settings.FACEBOOK_PAGE,
                connection_name='instant_articles',
                html_source=html,
                published=False,
                development_mode=False)
            messages.success(
                request,
                _('Instant Article published as ID %s' % article['id']))
            return HttpResponseRedirect(reverse(
                'admin:aldryn_newsblog_article_changelist',
                current_app=self.admin_site.name,
            ))
        else:
            opts = self.model._meta
            app_label = opts.app_label
            context = dict(
                self.admin_site.each_context(request),
                title=_('Are you sure?'),
                object_name=opts.verbose_name,
                object=obj,
                opts=opts,
                app_label=app_label,
                preserved_filters=self.get_preserved_filters(request),
                is_popup=(admin.options.IS_POPUP_VAR in request.POST or
                          admin.options.IS_POPUP_VAR in request.GET),
            )
            return render_to_response(
                self.publish_template,
                context,
                context_instance=RequestContext(request))

admin.site.unregister(Article)
admin.site.register(Article, InstantArticleAdmin)
