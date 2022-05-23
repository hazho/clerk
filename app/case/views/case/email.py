import re
import os
from typing import List
from django.utils.text import slugify

from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.html import strip_tags
from html_sanitizer import Sanitizer
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.db.models import Q
from bs4 import BeautifulSoup
from rest_framework.decorators import api_view
from rest_framework.response import Response


from core.models import Issue
from case.views.auth import paralegal_or_better_required
from emails.service import build_clerk_address
from emails.models import (
    EmailState,
    Email,
    EmailTemplate,
    EmailAttachment,
    SharepointState,
)
from case.forms import EmailForm
from case.utils import merge_form_data
from case.utils.router import Router
from microsoft.endpoints import MSGraphAPI
from microsoft.service import save_email_attachment
from case.utils.react import render_react_page
from case.serializers import IssueSerializer, EmailSerializer, EmailAttachmentSerializer


DISPLAY_EMAIL_STATES = [EmailState.SENT, EmailState.INGESTED]
DRAFT_EMAIL_STATES = [EmailState.READY_TO_SEND, EmailState.DRAFT]

router = Router("email")
router.create_route("list").uuid("pk")
router.create_route("thread").uuid("pk").path("thread").slug("slug")
router.create_route("draft").uuid("pk").path("draft")
router.create_route("edit").uuid("pk").path("draft").pk("email_pk")
router.create_route("send").uuid("pk").path("draft").pk("email_pk").path("send")
router.create_route("preview").uuid("pk").path("draft").pk("email_pk").path("preview")
(
    router.create_route("attach")
    .uuid("pk")
    .path("draft")
    .pk("email_pk")
    .path("attachment")
    .pk("attach_pk", optional=True)
)
router.create_route("attach-upload").uuid("pk").pk("email_pk").pk("attach_pk")


@router.use_route("list")
@paralegal_or_better_required
@require_http_methods(["GET"])
def email_list_view(request, pk):
    issue = _get_issue_for_emails(request, pk)
    case_email_address = build_clerk_address(issue)
    email_threads = _get_email_threads(issue)
    context = {
        "issue": issue,
        "email_threads": email_threads,
        "case_email_address": case_email_address,
    }
    return render(request, "case/case/email/list.html", context)


@router.use_route("thread")
@paralegal_or_better_required
@require_http_methods(["GET"])
def email_thread_view(request, pk, slug):
    issue = _get_issue_for_emails(request, pk)
    case_email_address = build_clerk_address(issue)
    email_threads = [t for t in _get_email_threads(issue) if t.slug == slug]
    if email_threads:
        # Assume thread slugs are unique.
        email_thread = email_threads[0]
    else:
        raise Http404()
    context = {
        "issue": IssueSerializer(issue).data,
        "subject": email_thread.subject,
        "emails": EmailSerializer(email_thread.emails, many=True).data,
        "case_email_address": case_email_address,
        "case_email_list_url": reverse("case-email-list", args=(issue.pk,)),
    }
    return render_react_page(request, f"Case {issue.fileref}", "email-thread", context)


class EmailThread:
    def __init__(self, email: Email):
        self.emails = [email]
        self.subject = email.subject or "No Subject"
        self.slug = self.slugify_subject(self.subject)
        self.most_recent = email.created_at

    @staticmethod
    def slugify_subject(subject):
        sub = subject or "No Subject"
        sub_cleaned = re.sub(r"re\s*:\s*", "", sub, flags=re.IGNORECASE)
        return slugify(sub_cleaned)

    def count_drafts(self):
        return self._get_count(EmailState.DRAFT)

    def count_sent(self):
        return self._get_count(EmailState.SENT)

    def count_received(self):
        return self._get_count(EmailState.INGESTED)

    def _get_count(self, state):
        return len([e for e in self.emails if e.state == state])

    def is_email_in_thread(self, email: Email) -> bool:
        return self.slug == self.slugify_subject(email.subject)

    def add_email_if_in_thread(self, email: Email) -> bool:
        is_in_thread = self.is_email_in_thread(email)
        if is_in_thread:
            self.emails.append(email)
            if email.created_at > self.most_recent:
                self.most_recent = email.created_at

        return is_in_thread

    def __repr__(self):
        return f"EmailThread<{self.subject}>"


DISPLAY_EMAIL_STATES = [EmailState.DRAFT, EmailState.SENT, EmailState.INGESTED]


def _get_email_threads(issue) -> List[EmailThread]:
    email_qs = (
        issue.email_set.filter(state__in=DISPLAY_EMAIL_STATES)
        .prefetch_related("emailattachment_set")
        .order_by("created_at")
    )
    threads = []
    for email in email_qs:
        _process_email_for_display(email)

        # Assign each email to a thread
        is_in_a_thread = False
        for thread in threads:
            is_in_a_thread = thread.add_email_if_in_thread(email)
            if is_in_a_thread:
                break

        if not is_in_a_thread:
            threads.append(EmailThread(email))

    for thread in threads:
        thread.emails = sorted(thread.emails, key=lambda t: t.created_at, reverse=True)

    return sorted(threads, key=lambda t: t.most_recent, reverse=True)


IMAGE_SUFFIXES = [".jpg", ".jpeg", ".png", ".gif"]


def _process_email_for_display(email: Email):
    email.html = get_email_html(email)
    for attachment in email.emailattachment_set.all():
        attachment.file.display_name = os.path.basename(attachment.file.name)


@router.use_route("draft")
@paralegal_or_better_required
@require_http_methods(["GET", "POST"])
def email_draft_create_view(request, pk):
    issue = _get_issue_for_emails(request, pk)
    case_email_address = build_clerk_address(issue, email_only=True)
    case_emails = get_case_emails(issue)
    templates = EmailTemplate.objects.filter(
        Q(topic=issue.topic) | Q(topic="GENERAL")
    ).order_by("-created_at")
    for template in templates:
        # Annotate with url
        qs = request.GET.copy()
        qs["template"] = template.pk
        template.url = "?" + qs.urlencode()

    parent_email = None
    if request.method == "POST":
        default_data = {
            "from_address": case_email_address,
            "state": EmailState.DRAFT,
            "issue": issue,
            "sender": request.user,
        }
        data = merge_form_data(request.POST, default_data)
        form = EmailForm(data, files=request.FILES)
        if form.is_valid():
            email = form.save()
            messages.success(request, "Draft created")
            return redirect("case-email-edit", issue.pk, email.pk)
    else:
        # It's a GET request.
        parent_id = request.GET.get("parent")
        template_id = request.GET.get("template")
        initial = {}
        if parent_id:
            try:
                parent_email = Email.objects.get(id=parent_id)
                _process_email_for_display(parent_email)
                initial["subject"] = parent_email.subject
                if parent_email.state == EmailState.INGESTED:
                    initial["to_address"] = parent_email.from_address
                else:
                    initial["to_address"] = parent_email.to_address
            except Email.DoesNotExist:
                raise Http404()
        if template_id:
            try:
                template = EmailTemplate.objects.get(id=template_id)
                initial["text"] = template.text
                initial["subject"] = template.subject
            except EmailTemplate.DoesNotExist:
                raise Http404()

        form = EmailForm(initial=initial)

    context = {
        "issue": issue,
        "parent_email": parent_email,
        "form": form,
        "case_emails": case_emails,
        "case_email_address": case_email_address,
        "templates": templates,
        "is_disabled": False,
    }
    return render(request, "case/case/email/draft_create.html", context)


@router.use_route("edit")
@paralegal_or_better_required
@require_http_methods(["GET", "POST", "DELETE"])
def email_draft_edit_view(request, pk, email_pk):
    issue = _get_issue_for_emails(request, pk)
    email = _get_email_for_issue(issue, email_pk)
    if not email.state in DRAFT_EMAIL_STATES:
        return redirect("case-email-list", issue.pk)

    case_email_address = build_clerk_address(issue, email_only=True)
    case_emails = get_case_emails(issue)
    if request.method == "POST":
        default_data = {
            "from_address": case_email_address,
            "state": EmailState.DRAFT,
            "issue": issue,
            "sender": request.user,
        }
        data = merge_form_data(request.POST, default_data)
        form = EmailForm(data, instance=email, files=request.FILES)
        if form.is_valid():
            messages.success(request, "Draft saved.")
            email = form.save()
    elif request.method == "DELETE":
        email.delete()
        messages.success(request, "Draft deleted")
        return HttpResponse(
            headers={"HX-Redirect": reverse("case-email-list", args=(pk,))}
        )
    else:
        form = EmailForm(instance=email)

    api = MSGraphAPI()
    sharepoint_docs = api.folder.get_all_files(f"cases/{issue.id}")
    sharepoint_options = [
        {"name": doc["name"], "value": doc["id"]} for doc in sharepoint_docs
    ]
    context = {
        "issue": issue,
        "form": form,
        "case_emails": case_emails,
        "email": email,
        "case_email_address": case_email_address,
        "is_disabled": email.state != EmailState.DRAFT,
        "sharepoint_options": sharepoint_options,
    }
    return render(request, "case/case/email/draft_edit.html", context)


@router.use_route("preview")
@paralegal_or_better_required
@require_http_methods(["GET"])
def email_draft_preview_view(request, pk, email_pk):
    issue = _get_issue_for_emails(request, pk)
    email = _get_email_for_issue(issue, email_pk)
    if not email.state in DRAFT_EMAIL_STATES:
        return redirect("case-email-list", issue.pk)

    html = _render_email_template(email.html)
    return HttpResponse(html, "text/html", 200)


def _render_email_template(html):
    if html:
        soup = BeautifulSoup(html, parser="lxml", features="lxml")
        for p_tag in soup.find_all("p"):
            p_tag["style"] = "margin:0 0 12px 0;"

        for a_tag in soup.find_all("a"):
            a_tag["style"] = "color:#438fef;text-decoration:underline;"

        context = {"html": mark_safe(soup.body.decode_contents())}
    else:
        context = {"html": ""}
    return render_to_string("case/case/email/preview.html", context)


@router.use_route("send")
@paralegal_or_better_required
@require_http_methods(["POST"])
def email_draft_send_view(request, pk, email_pk):
    issue = _get_issue_for_emails(request, pk)
    email = _get_email_for_issue(issue, email_pk)
    if email.state == EmailState.DRAFT:
        email.state = EmailState.READY_TO_SEND
        email.html = _render_email_template(email.html)
        email.save()
    elif email.state == EmailState.SENT:
        # Redirect to list view
        messages.success(request, "Email sent")
        return HttpResponse(
            headers={"HX-Redirect": reverse("case-email-list", args=(pk,))}
        )
    elif email.state != EmailState.READY_TO_SEND:
        raise Http404()

    form = EmailForm(instance=email)
    context = {
        "issue": issue,
        "form": form,
        "email": email,
        "is_disabled": True,
    }
    return render(request, "case/case/email/_email_form.html", context)


@router.use_route("attach")
@paralegal_or_better_required
@require_http_methods(["DELETE"])
def email_attachment_view(request, pk, email_pk, attach_pk):
    """Delete the email attachment, return HTML fragment for htmx."""
    issue = _get_issue_for_emails(request, pk)
    email = _get_email_for_issue(issue, email_pk)
    if not email.state == EmailState.DRAFT:
        raise Http404()

    email.emailattachment_set.filter(id=attach_pk).delete()
    context = {"issue": issue, "email": email}
    return render(request, "case/case/email/_draft_attachments.html", context)


@router.use_route("attach-upload")
@paralegal_or_better_required
@api_view(["POST"])
def email_attachment_upload_view(request, pk, email_pk, attach_pk):
    """Save the attachment to Sharepoint"""
    issue = _get_issue_for_emails(request, pk)
    email = _get_email_for_issue(issue, email_pk)
    try:
        attachment = EmailAttachment.objects.get(pk=attach_pk)
    except EmailAttachment.DoesNotExist:
        raise Http404()

    attachment.sharepoint_state = SharepointState.UPLOADING
    attachment.save()
    save_email_attachment(email, attachment)
    attachment.sharepoint_state = SharepointState.UPLOADED
    attachment.save()
    return Response(data=EmailAttachmentSerializer(instance=attachment).data)


def _get_email_for_issue(issue, email_pk):
    try:
        return issue.email_set.get(pk=email_pk)
    except Email.DoesNotExist:
        raise Http404()


def _get_issue_for_emails(request, pk):
    try:
        return (
            Issue.objects.check_permissions(request)
            .prefetch_related("email_set__emailattachment_set")
            .get(pk=pk)
        )
    except Issue.DoesNotExist:
        raise Http404()


def get_case_emails(issue: Issue):
    tenancy = issue.client.tenancy_set.select_related("landlord", "agent").first()
    emails = [
        {
            "email": issue.client.email,
            "name": issue.client.get_full_name(),
            "role": "Client",
        }
    ]
    if tenancy.agent:
        emails.append(
            {
                "email": tenancy.agent.email,
                "name": tenancy.agent.full_name,
                "role": "Agent",
            }
        )
    if tenancy.landlord:
        emails.append(
            {
                "email": tenancy.landlord.email,
                "name": tenancy.landlord.full_name,
                "role": "Landlord",
            }
        )

    return emails


sanitizer = Sanitizer(
    {
        "tags": {
            "a",
            "b",
            "blockquote",
            "br",
            "div",
            "em",
            "h1",
            "h2",
            "h3",
            "hr",
            "i",
            "li",
            "ol",
            "p",
            "span",
            "strong",
            "sub",
            "sup",
            "ul",
            "img",
        },
        "attributes": {
            "a": ("href", "name", "target", "title", "id", "rel", "src", "style")
        },
        "empty": {"hr", "a", "br"},
        "separate": {"a", "p", "li"},
        "whitespace": {"br"},
        "keep_typographic_whitespace": False,
        "add_nofollow": False,
        "autolink": False,
    }
)


def get_email_html(email) -> str:
    if email.html:
        return sanitizer.sanitize(email.html)
    else:
        text = email.text.replace("\r", "")
        text = re.sub("\n(?!\n)", "<br/>", text)
        return "".join(
            [f"<p>{line}</p>" for line in strip_tags(text).split("\n") if line]
        )
