import pathlib
import yaml
from fastapi.openapi.utils import get_openapi

BASE = pathlib.Path(__file__).parent


def _read_yaml(p: pathlib.Path) -> dict:
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_docs(locale: str = "ko"):
    loc = BASE / locale
    tags = _read_yaml(loc / "tags.yml")
    comps = _read_yaml(loc / "components.yml")
    paths = {}

    for f in loc.glob("paths.*.yml"):
        d = _read_yaml(f)
        if not d:
            continue
        paths.update(d.get("paths", d))

    return {
        "tags": tags.get("tags", []),
        "components": comps.get("components", {}),
        "paths": paths,
    }


def inject_openapi(app, *, locale: str = "ko"):
    docs = load_docs(locale)
    app.openapi_tags = docs["tags"]

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version="1.0.0",
            description="Insty AI 백엔드 API 명세서",
            routes=app.routes,
        )

        schema.setdefault("components", {})
        schema["components"].setdefault("schemas", {})
        yaml_components = docs["components"]

        if "schemas" in yaml_components:
            schema["components"]["schemas"].update(yaml_components["schemas"])

        if "securitySchemes" in yaml_components:
            schema["components"].setdefault("securitySchemes", {})
            schema["components"]["securitySchemes"].update(yaml_components["securitySchemes"])

        if yaml_components.get("securitySchemes"):
            schema.setdefault("security", [])
            if not any("bearerAuth" in s for s in schema["security"]):
                schema["security"].append({"bearerAuth": []})

        for op_id, inject_data in docs["paths"].items():
            for path, methods in schema.get("paths", {}).items():
                for method, op in methods.items():
                    if op.get("operationId") == op_id:
                        for k, v in inject_data.items():
                            if k in ("responses", "requestBody"):
                                op.setdefault(k, {}).update(v)
                            else:
                                op[k] = v

        for yaml_path, yaml_item in docs["paths"].items():
            if yaml_path not in schema["paths"]:
                for path, methods in schema.get("paths", {}).items():
                    for method, op in methods.items():
                        if op.get("operationId") in yaml_item:
                            schema["paths"][yaml_path] = {method: op}

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
