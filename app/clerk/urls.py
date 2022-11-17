from django.conf.urls import include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from rest_framework import routers
from django.views.generic.base import RedirectView

from web import urls as web_urls
from emails import urls as email_urls
from caller.views import answer_view, collect_view, message_view
from core import views as core_views
from webhooks.views import jotform_form_view, webflow_form_view, intake_no_email_view

from web.models import BlogListPage

router = routers.SimpleRouter()
router.register("upload", core_views.UploadViewSet, basename="upload")
router.register("submission", core_views.SubmissionViewSet, basename="submission")

urlpatterns = [
    path("oauth/", include("social_django.urls", namespace="social")),
    path("admin/", admin.site.urls, name="admin"),
    # TODO: Move to caller
    path("caller/answer/", answer_view, name="caller-answer"),
    path("caller/collect/", collect_view, name="caller-collect"),
    path("caller/message/", message_view, name="caller-message"),
    # TODO: Move to webhooks
    path("api/webhooks/webflow-form/", webflow_form_view, name="webflow-form"),
    path("api/webhooks/jotform-form/", jotform_form_view, name="jotform-form"),
    path("api/webhooks/intake-noemail/", intake_no_email_view, name="intake-noemail"),
    # TODO: Move router to core
    path("api/", include(router.urls)),
    path("clerk/", include("case.urls")),
    re_path(r"^case/(?P<path>.*)", RedirectView.as_view(url="/clerk/%(path)s")),
    path("accounts/", include("accounts.urls")),
    path("email/", include(email_urls)),
    path("", include(web_urls)),
]

# Internationalized urls
urlpatterns += i18n_patterns(
    BlogListPage.as_path("blog"),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
        path("__debug__/", include("debug_toolbar.urls")),
    ]
