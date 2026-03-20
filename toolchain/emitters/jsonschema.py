from __future__ import annotations

from toolchain.compiler.loader import ModuleGraph

PRIMITIVE_MAP = {
    "Int": {"type": "integer"},
    "Float": {"type": "number"},
    "Decimal": {"type": "number"},
    "Bool": {"type": "boolean"},
    "String": {"type": "string"},
    "Bytes": {"type": "string", "contentEncoding": "base64"},
    "Instant": {"type": "string", "format": "date-time"},
    "Duration": {"type": "string"},
    "Uuid": {"type": "string", "format": "uuid"},
    "Email": {"type": "string", "format": "email"},
    "UserId": {"type": "string", "format": "uuid"},
    "TenantId": {"type": "string", "format": "uuid"},
    "Principal": {"type": "object"},
}


def _split_qualified(name: str) -> tuple[str | None, str]:
    if "." in name:
        left, right = name.rsplit(".", 1)
        return left, right
    return None, name


def _ref_name(current_module: str, type_name: str) -> str:
    qualifier, bare = _split_qualified(type_name)
    module_name = qualifier or current_module
    return f"{module_name}.{bare}"


def _type_schema(current_module: str, type_name: str, known_defs: set[str]) -> dict:
    qualifier, bare = _split_qualified(type_name)
    if qualifier is None and bare in PRIMITIVE_MAP:
        return dict(PRIMITIVE_MAP[bare])
    ref = _ref_name(current_module, type_name)
    if ref in known_defs:
        return {"$ref": f"#/$defs/{ref}"}
    if bare in PRIMITIVE_MAP:
        return dict(PRIMITIVE_MAP[bare])
    return {"type": "object", "title": type_name}


def emit_json_schema(module_graph: ModuleGraph) -> dict:
    defs: dict[str, dict] = {}
    known_defs: set[str] = set()
    for module_name, loaded in module_graph.modules.items():
        for decl in [*loaded.module.schemas, *loaded.module.commands, *loaded.module.events]:
            known_defs.add(f"{module_name}.{decl.name}")

    for module_name, loaded in module_graph.modules.items():
        for decl in [*loaded.module.schemas, *loaded.module.commands, *loaded.module.events]:
            properties = {field.name: _type_schema(module_name, field.type_name, known_defs) for field in decl.fields}
            defs[f"{module_name}.{decl.name}"] = {
                "type": "object",
                "title": f"{module_name}.{decl.name}",
                "properties": properties,
                "required": sorted(properties.keys()),
                "additionalProperties": False,
            }
        for decl in loaded.module.type_aliases:
            defs[f"{module_name}.{decl.name}"] = _type_schema(module_name, decl.target_type, known_defs)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Astra Workspace Definitions",
        "$defs": defs,
    }
