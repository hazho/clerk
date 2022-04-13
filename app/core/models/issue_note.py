from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.db import transaction

from accounts.models import User

from .issue import Issue
from .timestamped import TimestampedModel


class NoteType(models.TextChoices):
    # A public file note.
    PARALEGAL = "PARALEGAL", "File note"
    # A case review by coordinators, for coordinators
    REVIEW = "REVIEW", "Case review"
    # A review of the paralegal's performance on a given case.
    PERFORMANCE = "PERFORMANCE", "Paralegal performance review"
    # An event generated by a user action
    EVENT = "EVENT", "System generated event"
    # An event related to an email
    EMAIL = "EMAIL", "Email"
    # An event related to a conflict check.
    CONFLICT_CHECK_SUCCESS = "CONFLICT_CHECK_SUCCESS", "Conflict check cleared"
    CONFLICT_CHECK_FAILURE = "CONFLICT_CHECK_FAILURE", "Conflict check not cleared"
    # An event related to an elgibility check
    ELIGIBILITY_CHECK_SUCCESS = "ELIGIBILITY_CHECK_SUCCESS", "Eligibility check cleared"
    ELIGIBILITY_CHECK_FAILURE = (
        "ELIGIBILITY_CHECK_FAILURE",
        "Eligibility check not cleared",
    )


class IssueNote(TimestampedModel):
    """
    A note, taken against a issue.
    """

    PARALEGAL_NOTE_TYPES = [
        NoteType.PARALEGAL,
        NoteType.EVENT,
        NoteType.EMAIL,
        NoteType.CONFLICT_CHECK_SUCCESS,
        NoteType.CONFLICT_CHECK_FAILURE,
        NoteType.ELIGIBILITY_CHECK_SUCCESS,
        NoteType.ELIGIBILITY_CHECK_FAILURE,
    ]
    COORDINATOR_NOTE_TYPES = [
        NoteType.PARALEGAL,
        NoteType.REVIEW,
        NoteType.PERFORMANCE,
        NoteType.EVENT,
        NoteType.EMAIL,
        NoteType.CONFLICT_CHECK_SUCCESS,
        NoteType.CONFLICT_CHECK_FAILURE,
        NoteType.ELIGIBILITY_CHECK_SUCCESS,
        NoteType.ELIGIBILITY_CHECK_FAILURE,
    ]

    # The case that this note is for
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)

    # Who made the note
    creator = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)

    # What kind of note this is.
    note_type = models.CharField(max_length=32, choices=NoteType.choices)

    # The text content of the note
    text = models.CharField(max_length=4096, blank=True, default="")

    # An optional event time, which can be interpreted based on what kind of note this is:
    #  - Review: the time to next review this case.
    event = models.DateTimeField(null=True, blank=True)

    # Optinal Actionstep ID, for file notes imported from Actionstep
    actionstep_id = models.IntegerField(blank=True, null=True)

    # A generic relation to a target object, this could be a paralegal or an issue event
    # See: https://simpleisbetterthancomplex.com/tutorial/2016/10/13/how-to-use-generic-relations.html
    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, on_delete=models.PROTECT
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey()

    def get_text(self):
        if self.note_type == NoteType.EVENT:
            return self.content_object.get_text()
        else:
            return self.text

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.note_type == NoteType.PERFORMANCE:
            # Set the paralegal as the issue target.
            if self.issue.paralegal:
                self.content_object = self.issue.paralegal

        super().save(*args, **kwargs)
