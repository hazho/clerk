from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.utils.datastructures import MultiValueDict
from django.contrib import messages
from django.urls import reverse
from rest_framework.decorators import api_view
from rest_framework.response import Response

from case.forms import (
    IssueProgressForm,
    ParalegalNoteForm,
    CaseReviewNoteForm,
    IssueAssignParalegalForm,
    IssueCloseForm,
    IssueOutcomeForm,
    ConflictCheckNoteForm,
    EligibilityCheckNoteForm,
    IssueReOpenForm,
    ParalegalReviewNoteForm,
)
from case.utils.router import Router
from case.views.auth import paralegal_or_better_required, coordinator_or_better_required
from core.models import Issue, IssueNote, Person
from core.models.issue_note import NoteType
from case.utils.react import render_react_page
from case.serializers import IssueSerializer, TenancySerializer, IssueNoteSerializer

MAYBE_IMAGE_FILE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

router = Router("detail")
router.create_route("view").uuid("pk")
router.create_route("note").uuid("pk").path("note")
router.create_route("review").uuid("pk").path("review")
router.create_route("performance").uuid("pk").path("performance")
router.create_route("conflict").uuid("pk").path("conflict")
router.create_route("eligibility").uuid("pk").path("eligibility")
router.create_route("assign").uuid("pk").path("assign")
router.create_route("progress").uuid("pk").path("progress")
router.create_route("close").uuid("pk").path("close")
router.create_route("reopen").uuid("pk").path("reopen")
router.create_route("outcome").uuid("pk").path("outcome")
router.create_route("landlord").uuid("pk").path("landlord").pk(
    "person_pk", optional=True
)
router.create_route("agent").uuid("pk").path("agent").pk("person_pk", optional=True)


@router.use_route("view")
@paralegal_or_better_required
@api_view(["GET"])
def case_detail_view(request, pk):
    """
    The details of a given case.
    """
    issue = _get_issue(request, pk)
    tenancy = _get_tenancy(issue)
    notes = _get_issue_notes(request, pk)
    file_urls, image_urls = _get_uploaded_files(issue)
    context = {
        "issue": IssueSerializer(issue).data,
        "tenancy": TenancySerializer(tenancy).data,
        "notes": IssueNoteSerializer(notes, many=True).data,
        "details": _get_submitted_details(issue),
        "file_urls": file_urls,
        "image_urls": image_urls,
        "actionstep_url": _get_actionstep_url(issue),
        "urls": {
            "detail": reverse("case-detail-view", args=(pk,)),
            "email": reverse("case-email-list", args=(pk,)),
            "docs": reverse("case-docs", args=(pk,)),
        },
        "permissions": {
            "is_paralegal_or_better": request.user.is_paralegal_or_better,
            "is_coordinator_or_better": request.user.is_coordinator_or_better,
        },
    }
    return render_react_page(request, f"Case {issue.fileref}", "case-detail", context)


@router.use_route("agent")
@paralegal_or_better_required
@api_view(["POST", "DELETE"])
def agent_selet_view(request, pk):
    """
    User can add or remove an agent for a given case.
    """
    return _person_select_view(request, pk, "agent")


@router.use_route("landlord")
@paralegal_or_better_required
@api_view(["POST", "DELETE"])
def landlord_selet_view(request, pk):
    """
    User can add or remove a landlord for a given case.
    """
    return _person_select_view(request, pk, "landlord")


def _person_select_view(request, pk, person_type):
    issue = _get_issue(request, pk)
    tenancy = _get_tenancy(issue)
    if request.method == "DELETE":
        # User is deleting the person from the tenancy.
        setattr(tenancy, person_type, None)
        tenancy.save()
    elif request.method == "POST":
        # User is adding a person from the tenancy.
        person_pk = request.data.get("person_id")
        if person_pk is None:
            return HttpResponseBadRequest()

        person = Person.objects.get(pk=int(person_pk))
        setattr(tenancy, person_type, person)
        tenancy.save()

    return Response(TenancySerializer(tenancy).data)


@router.use_route("note")
@paralegal_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_note_view(request, pk):
    """
    Form where paralegals can leave notes about case progress.
    """
    view = _build_case_note_view(
        ParalegalNoteForm,
        "note",
        "case/case/forms/_file_note.html",
        "File note created",
        NoteType.PARALEGAL,
    )
    return view(request, pk)


@router.use_route("review")
@coordinator_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_review_view(request, pk):
    """
    Form where coordinators can leave a note for other coordinators
    """
    view = _build_case_note_view(
        CaseReviewNoteForm,
        "review",
        "case/case/forms/_review_note.html",
        "Review note created",
        NoteType.REVIEW,
    )
    return view(request, pk)


@router.use_route("performance")
@coordinator_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_performance_view(request, pk):
    """
    Form where coordinators can leave a note on paralegal performance.
    """
    view = _build_case_note_view(
        ParalegalReviewNoteForm,
        "performance",
        "case/case/forms/_paralegal_review_note.html",
        "Review note created",
        NoteType.PERFORMANCE,
    )
    return view(request, pk)


def _build_case_note_view(Form, slug, template, success_message, note_type):
    """
    Returns a view that renders a form where you can add a type of note to the case
    """

    def case_note_view(request, pk):
        context = {}
        issue = _get_issue(request, pk)
        if request.method == "POST":
            default_data = {
                "issue": issue,
                "creator": request.user,
                "note_type": note_type,
            }
            form_data = _add_form_data(request.POST, default_data)
            form = Form(form_data)
            if form.is_valid():
                form.save()
                context.update({"notes": _get_issue_notes(request, pk)})
                messages.success(request, success_message)
        else:
            form = Form()

        url = reverse(f"case-detail-{slug}", args=(pk,))
        options_url = reverse("case-detail-options", args=(pk,))
        context.update(
            {"form": form, "issue": issue, "url": url, "options_url": options_url}
        )
        return render(request, template, context)

    return case_note_view


@router.use_route("conflict")
def case_detail_conflict_view(request, pk):
    """
    Form where coordinators can leave a note of a completed conflict check.
    """
    context = {}
    issue = _get_issue(request, pk)
    if request.method == "POST":
        default_data = {
            "issue": issue,
            "creator": request.user,
        }
        form_data = _add_form_data(request.POST, default_data)
        form = ConflictCheckNoteForm(form_data)
        if form.is_valid():
            form.save()
            context.update({"notes": _get_issue_notes(request, pk)})
            messages.success(request, "Conflict check record created")
    else:
        form = ConflictCheckNoteForm()

    url = reverse(f"case-detail-conflict", args=(pk,))
    options_url = reverse("case-detail-options", args=(pk,))
    context.update(
        {"form": form, "issue": issue, "url": url, "options_url": options_url}
    )
    return render(request, "case/case/forms/_conflict_check.html", context)


@router.use_route("eligibility")
def case_detail_eligibility_view(request, pk):
    """
    Form where coordinators can leave a note of a completed eligibility check.
    """
    context = {}
    issue = _get_issue(request, pk)
    if request.method == "POST":
        default_data = {
            "issue": issue,
            "creator": request.user,
        }
        form_data = _add_form_data(request.POST, default_data)
        form = EligibilityCheckNoteForm(form_data)
        if form.is_valid():
            form.save()
            context.update({"notes": _get_issue_notes(request, pk)})
            messages.success(request, "Eligibility check record created")
    else:
        form = EligibilityCheckNoteForm()

    url = reverse(f"case-detail-eligibility", args=(pk,))
    options_url = reverse("case-detail-options", args=(pk,))
    context.update(
        {"form": form, "issue": issue, "url": url, "options_url": options_url}
    )
    return render(request, "case/case/forms/_eligibility_check.html", context)


@router.use_route("assign")
@coordinator_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_assign_view(request, pk):
    """
    Form where coordinators can assign a paralegal to a case
    """
    context = {}
    issue = _get_issue(request, pk)
    if request.method == "POST":
        form = IssueAssignParalegalForm(request.POST, instance=issue)
        if form.is_valid():
            issue = form.save()
            context.update(
                {"new_paralegal": issue.paralegal, "new_lawyer": issue.lawyer}
            )
            messages.success(request, "Assignment successful")
    else:
        form = IssueAssignParalegalForm(instance=issue)

    url = reverse(f"case-detail-assign", args=(pk,))
    options_url = reverse(f"case-detail-options", args=(pk,))
    context.update(
        {"form": form, "issue": issue, "url": url, "options_url": options_url}
    )
    return render(request, "case/case/forms/_assign_paralegal.html", context)


@router.use_route("progress")
@paralegal_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_progress_view(request, pk):
    """
    Form where anyone can progress the case.
    """
    view = _build_case_update_view(
        IssueProgressForm,
        "progress",
        "case/case/forms/_progress.html",
        "Update successful",
    )
    return view(request, pk)


@router.use_route("close")
@coordinator_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_close_view(request, pk):
    """
    Form where you close the case.
    """
    view = _build_case_update_view(
        IssueCloseForm, "close", "case/case/forms/_close.html", "Case closed!"
    )
    return view(request, pk)


@router.use_route("reopen")
@coordinator_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_reopen_view(request, pk):
    """
    Form where you reopen the case.
    """
    view = _build_case_update_view(
        IssueReOpenForm, "reopen", "case/case/forms/_reopen.html", "Case re-opened"
    )
    return view(request, pk)


@router.use_route("outcome")
@coordinator_or_better_required
@require_http_methods(["GET", "POST"])
def case_detail_outcome_view(request, pk):
    """
    Form where you update the outcome of the case.
    """
    view = _build_case_update_view(
        IssueOutcomeForm, "outcome", "case/case/forms/_outcome.html", "Outcome updated"
    )
    return view(request, pk)


def _build_case_update_view(Form, slug, template, success_message):
    """
    Returns a view that renders a form where you update the case.
    """

    def case_update_view(request, pk):
        issue = _get_issue(request, pk)
        if request.method == "POST":
            form = Form(request.POST, instance=issue)
            if form.is_valid():
                issue = form.save()
                messages.success(request, success_message)
        else:
            form = Form(instance=issue)

        url = reverse(f"case-detail-{slug}", args=(pk,))
        options_url = reverse(f"case-detail-options", args=(pk,))
        context = {"form": form, "issue": issue, "url": url, "options_url": options_url}
        return render(request, template, context)

    return case_update_view


def _get_tenancy(issue):
    # FIXME: Assume only only tenancy but that's not how the models work.
    tenancy = issue.client.tenancy_set.first()
    return tenancy


def _get_issue(request, pk):
    try:
        issue = (
            Issue.objects.check_permissions(request)
            .select_related("client", "paralegal", "lawyer")
            .prefetch_related("fileupload_set")
            .get(pk=pk)
        )
    except Issue.DoesNotExist:
        raise Http404()

    return issue


def _get_uploaded_files(issue):
    file_urls, image_urls = [], []
    for upload in issue.fileupload_set.all():
        is_maybe_image = any(
            [upload.file.name.endswith(ext) for ext in MAYBE_IMAGE_FILE_EXTENSIONS]
        )
        if is_maybe_image:
            image_urls.append(upload.file.url)
        else:
            file_urls.append(upload.file.url)

    return file_urls or None, image_urls or None


def _get_submitted_details(issue):
    details = {}
    correct_case = lambda s: s.lower().capitalize()
    for name, answer in issue.answers.items():
        if answer is None:
            continue
        title = correct_case(" ".join(name.split("_")[1:]))
        answer = ", ".join(answer) if type(answer) is list else str(answer)
        if "_" in answer:
            answer = correct_case(" ".join(answer.split("_")))

        details[title] = answer

    return details


def _get_issue_notes(request, pk):
    """
    Returns the issue notes visible to a given user.
    """
    if request.user.is_coordinator_or_better:
        note_types = IssueNote.COORDINATOR_NOTE_TYPES
    else:
        note_types = IssueNote.PARALEGAL_NOTE_TYPES

    return (
        IssueNote.objects.filter(issue=pk)
        .prefetch_related("creator__groups")
        .filter(note_type__in=note_types)
        .order_by("-created_at")
        .all()
    )


def _get_actionstep_url(issue):
    if issue.actionstep_id:
        return f"https://ap-southeast-2.actionstep.com/mym/asfw/workflow/action/overview/action_id/{issue.actionstep_id}"


def _add_form_data(form_data, extra_data):
    return MultiValueDict({**{k: [v] for k, v in extra_data.items()}, **form_data})
