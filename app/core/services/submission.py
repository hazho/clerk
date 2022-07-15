import logging
from datetime import datetime

from django.db import transaction
from django.utils import timezone
from django_q.tasks import async_task
from utils.sentry import sentry_task

from core.models import Client, FileUpload, Issue, Person, Submission, Tenancy
from core.services.slack import send_submission_failure_slack

logger = logging.getLogger(__name__)


@sentry_task
def process_submission(sub_pk: str):
    """
    Convert a client's intake form submission into more meaningful relational objects:
        - Client: the client
        - Issue: the client's issues
        - FileUpload: files associated with an issue
        - Person: landlords and agents
        - Tenancy: the client's home

    """
    logger.info("Processing Submission[%s]", sub_pk)
    sub = Submission.objects.get(pk=sub_pk)
    answers = sub.answers
    try:
        with transaction.atomic():
            logger.info("Processing Client for Submission[%s]", sub_pk)
            try:
                client = process_client(answers)

                logger.info(
                    "Processed Client[%s] for Submission[%s]", client.pk, sub_pk
                )
            except Exception:
                logger.exception("Could not process Client for Submission[%s]")
                raise

            logger.info("Processing Tenancy for Submission[%s]", sub_pk)
            try:
                tenancy = process_tenancy(answers, client)
                logger.info(
                    "Processed Tenancy[%s] for Submission[%s]", tenancy.pk, sub_pk
                )
            except Exception:
                logger.exception("Could not process Tenancy for Submission[%s]")
                raise

            logger.info("Processing Issue for Submission[%s]", sub_pk)
            try:
                issue = process_issue(answers, client)
                logger.info("Processed Issue[%s] for Submission[%s]", issue.pk, sub_pk)
            except Exception:
                logger.exception("Could not process Issue for Submission[%s]", sub_pk)
                raise
    except Exception:
        logger.info("Sending failure notification for Submission[%s]", sub_pk)
        async_task(send_submission_failure_slack, sub_pk)
        raise

    Submission.objects.filter(pk=sub.pk).update(is_processed=True)


def process_issue(answers, client):
    topic = answers["ISSUES"]
    upload_answers = UPLOAD_ANSWERS[topic]
    issue_answers = {
        k: v
        for k, v in answers.items()
        if k.startswith(topic) and k not in upload_answers
    }
    issue_upload_ids = []
    for k in upload_answers:
        issue_upload_ids += [f["id"] for f in (answers.get(k) or [])]

    issue = Issue.objects.create(
        topic=topic,
        answers=issue_answers,
        client=client,
    )
    FileUpload.objects.filter(pk__in=issue_upload_ids).update(issue=issue.pk)
    return issue


UPLOAD_ANSWERS = {
    "REPAIRS": [
        "REPAIRS_ISSUE_PHOTO",
    ],
    "RENT_REDUCTION": [
        "RENT_REDUCTION_ISSUE_PHOTO",
        "RENT_REDUCTION_NOTICE_TO_VACATE_DOCUMENT",
    ],
    "EVICTION": ["EVICTIONS_DOCUMENTS_UPLOAD"],
    "BONDS": [
        "BONDS_RTBA_APPLICATION_UPLOAD",
        "BONDS_DAMAGE_QUOTE_UPLOAD",
        "BONDS_CLEANING_DOCUMENT_UPLOADS",
        "BONDS_LOCKS_CHANGE_QUOTE",
    ],
}


def process_client(answers):
    referrer = ""
    referrer = get_with_default(answers, "LEGAL_CENTER_REFERRER", referrer)
    referrer = get_with_default(answers, "HOUSING_SERVICE_REFERRER", referrer)
    referrer = get_with_default(answers, "CHARITY_REFERRER", referrer)
    referrer = get_with_default(answers, "SOCIAL_REFERRER", referrer)
    client, _ = Client.objects.get_or_create(
        email=answers["EMAIL"],
        defaults={
            "first_name": answers["FIRST_NAME"],
            "last_name": answers["LAST_NAME"],
            "date_of_birth": parse_date_string(answers["DOB"]),
            "phone_number": answers["PHONE"],
            "referrer_type": get_as_string(answers, "REFERRER_TYPE"),
            "referrer": referrer,
            "gender": answers["GENDER"],
            "primary_language_non_english": answers["CAN_SPEAK_NON_ENGLISH"],
            "is_aboriginal_or_torres_strait_islander": answers[
                "IS_ABORIGINAL_OR_TORRES_STRAIT_ISLANDER"
            ],
            "weekly_income": answers.get("WEEKLY_HOUSEHOLD_INCOME"),
            "employment_status": get_as_list(answers, "WORK_OR_STUDY_CIRCUMSTANCES"),
            "call_times": get_as_list(answers, "AVAILIBILITY"),
            "eligibility_circumstances": get_as_list(
                answers, "ELIGIBILITY_CIRCUMSTANCES"
            ),
            "rental_circumstances": answers["RENTAL_CIRCUMSTANCES"],
            "number_of_dependents": answers.get("NUMBER_OF_DEPENDENTS"),
            "primary_language": get_as_string(answers, "FIRST_LANGUAGE"),
            "requires_interpreter": get_as_bool(answers, "INTERPRETER"),
            "centrelink_support": get_as_bool(answers, "CENTRELINK_SUPPORT"),
            "eligibility_notes": get_as_string(answers, "ELIGIBILITY_NOTES"),
        },
    )
    return client


def process_tenancy(answers, client):
    agent = None
    landlord = None
    if answers.get("AGENT_NAME"):
        agent = Person.objects.create(
            full_name=answers["AGENT_NAME"].title(),
            address=answers["AGENT_ADDRESS"],
            email=answers["AGENT_EMAIL"],
            phone_number=answers["AGENT_PHONE"],
        )

    if answers.get("LANDLORD_NAME"):
        landlord = Person.objects.create(
            full_name=answers["LANDLORD_NAME"].title(),
            address=answers.get("LANDLORD_ADDRESS") or "",
            email=answers.get("LANDLORD_EMAIL") or "",
            phone_number=answers.get("LANDLORD_PHONE") or "",
        )

    tenancy, _ = Tenancy.objects.get_or_create(
        address=answers["ADDRESS"],
        client=client,
        defaults={
            "is_on_lease": answers["IS_ON_LEASE"],
            "started": parse_date_string(answers["START_DATE"]),
            "landlord": landlord,
            "agent": agent,
            "postcode": answers["POSTCODE"],
            "suburb": answers["SUBURB"],
        },
    )
    return tenancy


def parse_date_string(s: str):
    # 1995-6-6
    dt = datetime.strptime(s, "%Y-%m-%d")
    tz = timezone.get_current_timezone()
    dt = timezone.make_aware(dt, timezone=tz)
    return dt.replace(hour=0, minute=0)


def get_as_list(answers, key):
    val = answers.get(key)
    if type(val) is list:
        return val
    elif not val:
        return []
    else:
        return [val]


def get_as_bool(answers, key):
    return answers.get(key, False) or False


def get_as_string(answers, key):
    return answers.get(key) or ""


def get_with_default(answers, key, default):
    return answers.get(key) or default
