from wagtail.core import blocks
from wagtail.core.models import Page
from wagtail.core.fields import StreamField
from wagtail.admin.edit_handlers import StreamFieldPanel
from .mixins import RICH_TEXT_FEATURES, NotFoundMixin


class ResourceListPage(NotFoundMixin, Page):
    subpage_types = ["web.ResourcePage"]
    parent_page_types = ["web.RootPage"]


class ResourcePage(Page):
    template = "web/resources/resource-page.html"
    parent_page_types = ["web.ResourceListPage"]
    subpage_types = []

    body = StreamField(
        [
            ("heading", blocks.CharBlock(form_classname="full title")),
            ("paragraph", blocks.RichTextBlock(features=RICH_TEXT_FEATURES)),
        ]
    )
    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
    ]
