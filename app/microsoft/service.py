import logging

from django.conf import settings
from django.utils import timezone

from accounts.models import User
from core.models import CaseTopic, Issue, FileUpload
from microsoft.endpoints import MSGraphAPI

logger = logging.getLogger(__name__)


# Paths for template folders.
TEMPLATE_PATHS = {
    CaseTopic.BONDS: "templates/bonds",
    CaseTopic.REPAIRS: "templates/repairs",
    CaseTopic.EVICTION: "templates/evictions",
}
CLIENT_UPLOAD_FOLDER_NAME = "client-uploads"


def get_user_permissions(user):
    api = MSGraphAPI()
    ms_account = api.user.get(user.email)
    has_coordinator_perms = False
    paralegal_perm_issues = []
    paralegal_perm_missing_issues = []

    if ms_account:
        members = api.group.members()
        has_coordinator_perms = user.email in members
        for issue in Issue.objects.filter(paralegal=user).all():
            case_path = f"cases/{issue.id}"
            permissions = api.folder.list_permissions(case_path)
            has_access = False
            for perm in permissions or []:
                _, perm_data = perm
                email = perm_data.get("user", {}).get("email")
                if email == user.email:
                    has_access = True
            if has_access:
                paralegal_perm_issues.append(issue)
            else:
                paralegal_perm_missing_issues.append(issue)

    return {
        "has_coordinator_perms": has_coordinator_perms,
        "paralegal_perm_issues": paralegal_perm_issues,
        "paralegal_perm_missing_issues": paralegal_perm_missing_issues,
    }


def set_up_new_user(user):
    """
    Create MS account for new user and assign license.
    """
    api = MSGraphAPI()
    ms_account = api.user.get(user.email)

    if not ms_account:
        _, password = api.user.create(user.first_name, user.last_name, user.email)
        api.user.assign_license(user.email)
        User.objects.filter(pk=user.pk).update(ms_account_created_at=timezone.now())
        return password


def set_up_new_case(issue: Issue):
    """
    Make a copy of the relevant templates folder with the name of the new case.
    """
    api = MSGraphAPI()
    case_folder_name = str(issue.id)
    parent_folder_id = settings.CASES_FOLDER_ID
    template_path = TEMPLATE_PATHS[issue.topic]
    # Copy templates to the case folder if not already done.
    case_folder = api.folder.get_child_if_exists(case_folder_name, parent_folder_id)
    if not case_folder:
        logger.info("Creating case folder for Issue<%s>", issue.pk)
        case_folder = api.folder.copy(template_path, case_folder_name, parent_folder_id)
    else:
        logger.info("Case folder already exists for Issue<%s>", issue.pk)

    # Copy client uploaded files to the case folder
    file_uploads = FileUpload.objects.filter(issue=issue).all()
    if file_uploads.exists():
        uploads_folder = api.folder.get_child_if_exists(
            CLIENT_UPLOAD_FOLDER_NAME, case_folder["id"]
        )
        if not uploads_folder:
            logger.info("Creating intake uploads folder for Issue<%s>", issue.pk)
            uploads_folder = api.folder.create_folder(
                CLIENT_UPLOAD_FOLDER_NAME, case_folder["id"]
            )
        else:
            logger.info("Intake uploads folder already exists for Issue<%s>", issue.pk)

        for file_upload in file_uploads:
            name = file_upload.file.name.split("/")[1]
            logger.info(
                "Uploading case file %s to Sharepoint for Issue<%s>", name, issue.pk
            )
            api.folder.upload_file(file_upload.file, uploads_folder["id"], name=name)


def add_user_to_case(user, issue):
    """
    Give User write permissions for a specific case (folder).
    """
    api = MSGraphAPI()
    case_path = f"cases/{issue.id}"
    api.folder.create_permissions(case_path, "write", [user.email])


def remove_user_from_case(user, issue):
    """
    Delete the permissions that a User has for a specific case (folder).
    """
    api = MSGraphAPI()
    case_path = f"cases/{issue.id}"

    # Get the permissions for the case.
    permissions = api.folder.list_permissions(case_path)

    # Iterate through the permissions and delete those belonging to the User.
    if permissions:
        for perm_id, user_object in permissions:
            email = user_object["user"].get("email")
            if email == user.email:
                api.folder.delete_permission(case_path, perm_id)


def get_case_folder_info(issue):
    """
    Return a tuple containing the case folder's list of files and URL.
    """
    api = MSGraphAPI()

    case_path = f"cases/{issue.id}"

    # Get the list of files (name, file URL) for the case folder.
    json = api.folder.get_children(case_path)

    list_files = []

    if json:
        for item in json["value"]:
            list_files.append((item["name"], item["webUrl"]))

    # Get the case folder URL.
    folder = api.folder.get(case_path)
    folder_url = folder["webUrl"] if folder else None

    return list_files, folder_url


def set_up_coordinator(user):
    """
    Add User as Group member.
    """
    api = MSGraphAPI()

    members = api.group.members()

    if user.email not in members:
        api.group.add_user(user.email)


def tear_down_coordinator(user):
    """
    Remove User as Group member.
    """
    api = MSGraphAPI()

    members = api.group.members()

    if user.email in members:
        result = api.user.get(user.email)
        user_id = result["id"]
        api.group.remove_user(user_id)


def list_templates(topic):
    api = MSGraphAPI()
    path = TEMPLATE_PATHS[topic]
    results = api.folder.get_children(path)
    return [
        {
            "id": doc["id"],
            "name": doc["name"],
            "url": doc["webUrl"],
            "created_at": timezone.datetime.fromisoformat(
                doc["createdDateTime"].replace("Z", "")
            ).strftime("%d/%m/%Y"),
            "modified_at": timezone.datetime.fromisoformat(
                doc["lastModifiedDateTime"].replace("Z", "")
            ).strftime("%d/%m/%Y"),
        }
        for doc in results["value"]
    ]


def upload_template(topic, file):
    api = MSGraphAPI()
    path = TEMPLATE_PATHS[topic]
    parent = api.folder.get(path)
    api.folder.upload_file(file, parent["id"])


def delete_template(file_id):
    api = MSGraphAPI()
    api.folder.delete_file(file_id)
