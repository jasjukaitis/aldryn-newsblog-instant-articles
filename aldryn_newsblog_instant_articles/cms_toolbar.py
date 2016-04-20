from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool

from aldryn_apphooks_config.utils import get_app_instance
from aldryn_newsblog.cms_appconfig import NewsBlogConfig
from aldryn_newsblog.models import Article
from aldryn_translation_tools.utils import (
    get_object_from_request,
    get_admin_url,
)


@toolbar_pool.register
class InstantArticleNewsBlogToolbar(CMSToolbar):

    def __get_newsblog_config(self):
        try:
            __, config = get_app_instance(self.request)
            if not isinstance(config, NewsBlogConfig):
                # This is not the app_hook you are looking for.
                return None
        except ImproperlyConfigured:
            # There is no app_hook at all.
            return None

        return config

    def populate(self):
        config = self.__get_newsblog_config()
        if not config:
            return
        try:
            view_name = self.request.resolver_match.view_name
        except AttributeError:
            return
        user = getattr(self.request, 'user', None)
        if user and view_name:
            if view_name == '{0}:article-detail'.format(config.namespace):
                article = get_object_from_request(Article, self.request)
            else:
                article = None
            menu = self.toolbar.get_or_create_menu('newsblog-app',
                                                   config.get_app_title())
            delete_article_perm = user.has_perm(
                'aldryn_newsblog.delete_article')
            if delete_article_perm and article:
                url = get_admin_url(
                    'aldryn_newsblog_article_publish_instant_article',
                    [article.pk, ])
                menu.add_break()
                menu.add_modal_item(_('Publish Instant Article'), url=url)
