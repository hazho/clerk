import json

from django.shortcuts import render
from django.conf import settings


def render_react_page(request, title, react_page_name, react_context, public=False):
    react_context.update(
        {
            "user": {
                "is_admin": request.user.is_admin,
                "is_coordinator": request.user.is_coordinator,
                "is_paralegal": request.user.is_paralegal,
                "is_admin_or_better": request.user.is_admin_or_better,
                "is_coordinator_or_better": request.user.is_coordinator_or_better,
                "is_paralegal_or_better": request.user.is_paralegal_or_better,
            }
        }
    )
    context = {
        "SENTRY_JS_DSN": settings.SENTRY_JS_DSN,
        "react_context": json.dumps(react_context),
        "react_page_name": react_page_name,
        "title": title,
        "public": public,
    }
    return render(request, "case/react_base.html", context)


def is_react_api_call(request):
    return bool(request.META.get("HTTP_X_REACT"))
