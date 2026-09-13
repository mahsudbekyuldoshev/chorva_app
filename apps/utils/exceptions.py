from rest_framework.exceptions import APIException, Throttled
from rest_framework.views import exception_handler

ERROR_CODE_MAP = {
    "ValidationError": "VALIDATION_ERROR",
    "AuthenticationFailed": "AUTHENTICATION_FAILED",
    "NotAuthenticated": "NOT_AUTHENTICATED",
    "PermissionDenied": "PERMISSION_DENIED",
    "NotFound": "NOT_FOUND",
    "Http404": "NOT_FOUND",
    "Throttled": "THROTTLED",
    "ParseError": "PARSE_ERROR",
    "MethodNotAllowed": "METHOD_NOT_ALLOWED",
    "RelistCooldownError": "RELIST_COOLDOWN",
}


class RelistCooldownError(APIException):
    status_code = 400
    default_detail = "Qayta ko'tarish uchun hali vaqt kerak."
    default_code = "relist_cooldown"


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data and len(data) == 1:
            return str(data["detail"])
        parts = []
        for field, errors in data.items():
            if isinstance(errors, list) and errors:
                parts.append(f"{field}: {errors[0]}")
            else:
                parts.append(f"{field}: {errors}")
        return "; ".join(parts) if parts else "Xatolik yuz berdi."
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data) if data else "Xatolik yuz berdi."


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    code = ERROR_CODE_MAP.get(exc.__class__.__name__, "ERROR")
    message = _extract_message(response.data)

    extra = {}
    if isinstance(exc, Throttled) and exc.wait:
        extra["retry_after_seconds"] = int(exc.wait)

    response.data = {"code": code, "message": message, **extra}
    return response
