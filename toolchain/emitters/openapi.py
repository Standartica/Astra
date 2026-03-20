from __future__ import annotations

from toolchain.compiler.loader import ModuleGraph
from toolchain.emitters.jsonschema import emit_json_schema


def _split_qualified(name: str) -> tuple[str | None, str]:
    if "." in name:
        left, right = name.rsplit(".", 1)
        return left, right
    return None, name


def _component_ref(current_module: str, type_name: str) -> str:
    qualifier, bare = _split_qualified(type_name)
    module_name = qualifier or current_module
    return f"#/components/schemas/{module_name}.{bare}"


def emit_openapi(module_graph: ModuleGraph) -> dict:
    json_schema = emit_json_schema(module_graph)
    components = {"schemas": dict(json_schema.get("$defs", {}))}
    paths: dict[str, dict] = {}

    query_index: dict[tuple[str, str], object] = {}
    command_index: dict[tuple[str, str], object] = {}
    for module_name, loaded in module_graph.modules.items():
        for query in loaded.module.queries:
            query_index[(module_name, query.name)] = query
        for command in loaded.module.commands:
            command_index[(module_name, command.name)] = command

    for module_name, loaded in module_graph.modules.items():
        for api in loaded.module.apis:
            for route in api.routes:
                operation: dict = {
                    "operationId": f"{module_name}.{api.name}.{route.target}",
                    "responses": {"200": {"description": "Successful response"}},
                }
                route_key = route.path
                method_key = route.method.lower()
                qualifier, bare = _split_qualified(route.target)
                target_module = qualifier or module_name
                if (target_module, bare) in command_index:
                    operation["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": _component_ref(target_module, bare)}
                            }
                        },
                    }
                    operation["responses"] = {"202": {"description": "Accepted"}}
                elif (target_module, bare) in query_index:
                    query = query_index[(target_module, bare)]
                    if query.output_type:
                        operation["responses"] = {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": _component_ref(target_module, query.output_type)}
                                    }
                                },
                            }
                        }
                paths.setdefault(route_key, {})[method_key] = operation

    return {
        "openapi": "3.1.0",
        "info": {"title": "Astra Generated API", "version": "0.1.0"},
        "paths": paths,
        "components": components,
    }
