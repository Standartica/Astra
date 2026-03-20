from __future__ import annotations

from dataclasses import dataclass, field

from toolchain.compiler.artifact_graph import _exported_symbol_maps
from toolchain.compiler.diagnostics import DiagnosticBag
from toolchain.compiler.loader import ModuleGraph


@dataclass(slots=True)
class CompatibilityResult:
    previous_count: int
    current_count: int
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)


def _artifact_map(graph: ModuleGraph) -> dict[str, dict]:
    exported = _exported_symbol_maps(graph)
    result: dict[str, dict] = {}
    for module_name, loaded in graph.modules.items():
        visible = exported.get(module_name, {})
        for decl in loaded.module.type_aliases:
            if decl.name in visible:
                result[f"{module_name}.type.{decl.name}"] = {"kind": "type", "target": decl.target_type}
        for decl in loaded.module.schemas:
            if decl.name in visible:
                result[f"{module_name}.schema.{decl.name}"] = {"kind": "schema", "fields": {f.name: f.type_name for f in decl.fields}}
        for decl in loaded.module.commands:
            if decl.name in visible:
                result[f"{module_name}.command.{decl.name}"] = {"kind": "command", "fields": {f.name: f.type_name for f in decl.fields}}
        for decl in loaded.module.events:
            if decl.name in visible:
                result[f"{module_name}.event.{decl.name}"] = {"kind": "event", "fields": {f.name: f.type_name for f in decl.fields}}
        for decl in loaded.module.queries:
            if decl.name in visible:
                result[f"{module_name}.query.{decl.name}"] = {"kind": "query", "input": decl.input_type, "output": decl.output_type}
        for decl in loaded.module.apis:
            if decl.name in visible:
                result[f"{module_name}.api.{decl.name}"] = {"kind": "api", "routes": {(r.method.lower(), r.path): r.target for r in decl.routes}}
    return result


def compare_module_graphs(previous: ModuleGraph, current: ModuleGraph) -> CompatibilityResult:
    prev = _artifact_map(previous)
    cur = _artifact_map(current)
    result = CompatibilityResult(previous_count=len(prev), current_count=len(cur))

    for key, prev_item in prev.items():
        cur_item = cur.get(key)
        if cur_item is None:
            result.diagnostics.add("error", "ASTRA6001", f"Exported artifact removed: {key}")
            continue
        if prev_item["kind"] != cur_item["kind"]:
            result.diagnostics.add("error", "ASTRA6002", f"Artifact kind changed for {key}")
            continue
        if prev_item["kind"] in {"schema", "command", "event"}:
            prev_fields = prev_item["fields"]
            cur_fields = cur_item["fields"]
            for field_name, field_type in prev_fields.items():
                if field_name not in cur_fields:
                    result.diagnostics.add("error", "ASTRA6003", f"Field removed: {key}.{field_name}")
                elif cur_fields[field_name] != field_type:
                    result.diagnostics.add("error", "ASTRA6004", f"Field type changed: {key}.{field_name}")
            for field_name in cur_fields.keys() - prev_fields.keys():
                result.diagnostics.add("info", "ASTRA6101", f"Field added: {key}.{field_name}")
        elif prev_item["kind"] == "type":
            if prev_item["target"] != cur_item["target"]:
                result.diagnostics.add("error", "ASTRA6005", f"Type alias target changed for {key}")
        elif prev_item["kind"] == "query":
            if prev_item["input"] != cur_item["input"]:
                result.diagnostics.add("error", "ASTRA6006", f"Query input changed for {key}")
            if prev_item["output"] != cur_item["output"]:
                result.diagnostics.add("error", "ASTRA6007", f"Query output changed for {key}")
        elif prev_item["kind"] == "api":
            prev_routes = prev_item["routes"]
            cur_routes = cur_item["routes"]
            for route_key, target in prev_routes.items():
                if route_key not in cur_routes:
                    result.diagnostics.add("error", "ASTRA6008", f"API route removed: {key} {route_key[0].upper()} {route_key[1]}")
                elif cur_routes[route_key] != target:
                    result.diagnostics.add("error", "ASTRA6009", f"API route target changed: {key} {route_key[0].upper()} {route_key[1]}")
            for route_key in cur_routes.keys() - prev_routes.keys():
                result.diagnostics.add("info", "ASTRA6102", f"API route added: {key} {route_key[0].upper()} {route_key[1]}")

    for key in cur.keys() - prev.keys():
        result.diagnostics.add("info", "ASTRA6201", f"New exported artifact added: {key}")

    return result
