# flake8: noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *

IS_PROD = True
DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = [
    "www.anikalegal.com",
    "clerk.anikalegal.com",  # TODO: Remove
    "127.0.0.1",
    "localhost",
]

EMAIL_PREFIX = None
WEBMASTER_EMAIL = "webmaster@anikalegal.com"
SUBMISSION_EMAILS = [WEBMASTER_EMAIL]
INTAKE_NOEMAIL_EMAIL = "coordinators@anikalegal.com"

SESSION_COOKIE_DOMAIN = ".anikalegal.com"
SESSION_SAVE_EVERY_REQUEST = True
CSRF_COOKIE_DOMAIN = ".anikalegal.com"
CSRF_TRUSTED_ORIGINS = ["https://*.anikalegal.com"]
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_REGEX_WHITELIST = (
    r"^(https?://)?(\w*-*\w*\.+)*anikalegal\.com$",
    r"^(https?://)?(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d{4})?$",
)

# Turn off browsable DRF API in prod.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)

# Get DRF to use HTTPS in links.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

AWS_STORAGE_BUCKET_NAME = "anika-clerk"


sentry_sdk.init(
    dsn=os.environ.get("RAVEN_DSN"),
    integrations=[DjangoIntegration()],
    environment="prod",
)


ADMIN_PREFIX = "prod"

# Reminder Email for MailChimp
MAILCHIMP_COVID_LIST_ID = "9749f1f08c"
MAILCHIMP_COVID_WORKFLOW_ID = "fb4daa69fe"
MAILCHIMP_COVID_EMAIL_ID = "e8ae8c5b35"
MAILCHIMP_REPAIRS_LIST_ID = "aa24ab1b75"
MAILCHIMP_REPAIRS_WORKFLOW_ID = "3bd9c82043"
MAILCHIMP_REPAIRS_EMAIL_ID = "04fb17ccee"

# Call Centre powered by Twilio
TWILIO_PHONE_NUMBER = "+61480016398"
TWILIO_AUDIO_BASE_URL = "https://anika-twilio-audio.s3-ap-southeast-2.amazonaws.com"

# Transactional emails via SendGrid
EMAIL_DOMAIN = "em9037.mail.anikalegal.com"

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# Google Analytics
GOOGLE_ANALYTICS_ID = "UA-133303109-1"
FACEBOOK_PIXEL_ID = "580273702543728"

# MS Graph Integration
MS_GRAPH_GROUP_ID = "565f3cd9-c16e-49a8-9bba-d2ac86fea77b"
MS_GRAPH_DRIVE_ID = "b!83_G5n94RUKVhtqomh8QdLsJLbi6tCpKomnhyRvhq7L3St3-kEDdTq9Ft70M4eXu"
CASES_FOLDER_ID = "017MQILZDHEEIISZQLR5HZOMU4KKAUM34D"
MS_REMOVE_OFFICE_LICENCES = True

SLACK_EMAIL_ALERT_OVERRIDE = None
CLERK_BASE_URL = "https://www.anikalegal.com"
