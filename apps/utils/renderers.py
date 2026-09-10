from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """Barcha javoblarni mobil ilova kutgan umumiy qobiqqa o'raydi.

    Muvaffaqiyatli: {"success": true, "data": <asl data>}
    Xatolik:        {"success": false, "error": {"code": "...", "message": "..."}}
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")
        status_code = response.status_code if response is not None else 200

        if status_code >= 400:
            envelope = {"success": False, "error": data}
        else:
            envelope = {"success": True, "data": data}

        return super().render(envelope, accepted_media_type, renderer_context)
