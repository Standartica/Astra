from __future__ import annotations

from toolchain.compiler.loader import ModuleGraph
from toolchain.emitters.jsonschema import _split_qualified


def _find_query(module_graph: ModuleGraph, current_module: str, target: str):
    qualifier, bare = _split_qualified(target)
    module_name = qualifier or current_module
    loaded = module_graph.modules.get(module_name)
    if not loaded:
        return None
    return next((q for q in loaded.module.queries if q.name == bare), None)



def emit_server_stubs(module_graph: ModuleGraph) -> str:
    lines: list[str] = []
    lines.append('"""Auto-generated Astra server stubs."""')
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from dataclasses import dataclass")
    lines.append("from typing import Any")
    lines.append("")
    lines.append("@dataclass(slots=True)")
    lines.append("class RouteStub:")
    lines.append("    method: str")
    lines.append("    path: str")
    lines.append("    operation_id: str")
    lines.append("    request_model: str | None = None")
    lines.append("    response_model: str | None = None")
    lines.append("")
    lines.append("def build_routes() -> list[RouteStub]:")
    lines.append("    return [")
    for module_name, loaded in module_graph.modules.items():
        for api in loaded.module.apis:
            for route in api.routes:
                qualifier, bare = _split_qualified(route.target)
                target_module = qualifier or module_name
                request_model = None
                response_model = None
                if any(c.name == bare for c in module_graph.modules[target_module].module.commands):
                    request_model = bare
                query = _find_query(module_graph, module_name, route.target)
                if query and query.output_type:
                    response_model = query.output_type
                lines.append(
                    "        RouteStub(method=%r, path=%r, operation_id=%r, request_model=%r, response_model=%r),"
                    % (route.method.upper(), route.path, f"{module_name}.{api.name}.{route.target}", request_model, response_model)
                )
    lines.append("    ]")
    lines.append("")
    lines.append("def register_routes(app: Any) -> None:")
    lines.append("    for route in build_routes():")
    lines.append("        app.add_route(route.method, route.path, route.operation_id)")
    lines.append("")
    return "\n".join(lines)
