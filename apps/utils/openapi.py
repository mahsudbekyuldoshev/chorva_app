def envelope_postprocessing_hook(result, generator, request, public):
    """
    Generatsiya qilingan OpenAPI sxemasidagi har bir javobni
    {"success": ..., "data"/"error": ...} qobig'iga moslab qayta yozadi.
    """
    schemas = result.setdefault("components", {}).setdefault("schemas", {})

    schemas["ErrorEnvelope"] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
        },
    }

    for path_item in result.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            for status_code, response in operation["responses"].items():
                content = response.get("content", {}).get("application/json")
                if not content:
                    continue
                original_schema = content.get("schema")
                if status_code.startswith("2"):
                    content["schema"] = {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean", "example": True},
                            "data": original_schema or {},
                        },
                    }
                else:
                    content["schema"] = {"$ref": "#/components/schemas/ErrorEnvelope"}
    return result
