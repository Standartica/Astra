from __future__ import annotations

from dataclasses import dataclass, field

from toolchain.compiler.diagnostics import DiagnosticBag
from toolchain.compiler.loader import ModuleGraph
from toolchain.parser.ast import ApiDecl, CommandDecl, EventDecl, Module, QueryDecl, SchemaDecl


@dataclass(slots=True)
class ArtifactSignature:
    module: str
    name: str
    kind: str
    exported: bool = True
    fields: dict[str, str] = field(default_factory=dict)
    input_type: str | None = None
    output_type: str | None = None
    target_type: str | None = None
    routes: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class CompatibilityResult:
    previous_count: int
    current_count: int
    previous_signatures: dict[str, ArtifactSignature]
    current_signatures: dict[str, ArtifactSignature]
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)


DECL_ATTRS = {
    "type": "type_aliases",
    "schema": "schemas",
    "command": "commands",
    "event": "events",
    "query": "queries",
    "api": "apis",
}


def _exported_names(module: Module) -> set[str]:
    if module.exports:
        return {item.name for item in module.exports}
    names: set[str] = set()
    for attr in DECL_ATTRS.values():
        for decl in getattr(module, attr):
            names.add(decl.name)
    return names


def _field_map(decl: SchemaDecl | CommandDecl | EventDecl) -> dict[str, str]:
    return {field.name: field.type_name for field in decl.fields}


def _route_map(decl: ApiDecl) -> dict[str, str]:
    return {f"{route.method.lower()} {route.path}": route.target for route in decl.routes}


def collect_signatures(module_graph: ModuleGraph) -> dict[str, ArtifactSignature]:
    signatures: dict[str, ArtifactSignature] = {}
    for module_name, loaded in module_graph.modules.items():
        exported = _exported_names(loaded.module)

        for decl in loaded.module.type_aliases:
            if decl.name in exported:
                signatures[f"{module_name}:type:{decl.name}"] = ArtifactSignature(
                    module=module_name,
                    name=decl.name,
                    kind="type",
                    exported=True,
                    target_type=decl.target_type,
                )
        for decl in loaded.module.schemas:
            if decl.name in exported:
                signatures[f"{module_name}:schema:{decl.name}"] = ArtifactSignature(
                    module=module_name,
                    name=decl.name,
                    kind="schema",
                    exported=True,
                    fields=_field_map(decl),
                )
        for decl in loaded.module.commands:
            if decl.name in exported:
                signatures[f"{module_name}:command:{decl.name}"] = ArtifactSignature(
                    module=module_name,
                    name=decl.name,
                    kind="command",
                    exported=True,
                    fields=_field_map(decl),
                )
        for decl in loaded.module.events:
            if decl.name in exported:
                signatures[f"{module_name}:event:{decl.name}"] = ArtifactSignature(
                    module=module_name,
                    name=decl.name,
                    kind="event",
                    exported=True,
                    fields=_field_map(decl),
                )
        for decl in loaded.module.queries:
            if decl.name in exported:
                signatures[f"{module_name}:query:{decl.name}"] = ArtifactSignature(
                    module=module_name,
                    name=decl.name,
                    kind="query",
                    exported=True,
                    input_type=decl.input_type,
                    output_type=decl.output_type,
                )
        for decl in loaded.module.apis:
            if decl.name in exported:
                signatures[f"{module_name}:api:{decl.name}"] = ArtifactSignature(
                    module=module_name,
                    name=decl.name,
                    kind="api",
                    exported=True,
                    routes=_route_map(decl),
                )
    return signatures


def compare_module_graphs(previous: ModuleGraph, current: ModuleGraph) -> CompatibilityResult:
    prev = collect_signatures(previous)
    cur = collect_signatures(current)
    result = CompatibilityResult(
        previous_count=len(prev),
        current_count=len(cur),
        previous_signatures=prev,
        current_signatures=cur,
    )

    for key, old_sig in prev.items():
        new_sig = cur.get(key)
        label = f"{old_sig.module}.{old_sig.name}"
        if new_sig is None:
            result.diagnostics.add("error", "ASTRA6001", f"Exported artifact removed: {label} ({old_sig.kind})")
            continue
        if new_sig.kind != old_sig.kind:
            result.diagnostics.add("error", "ASTRA6002", f"Artifact kind changed for {label}: {old_sig.kind} -> {new_sig.kind}")
            continue

        if old_sig.kind in {"schema", "command", "event"}:
            old_fields = old_sig.fields
            new_fields = new_sig.fields
            for field_name in sorted(set(old_fields) - set(new_fields)):
                result.diagnostics.add("error", "ASTRA6003", f"Field removed from {old_sig.kind} {label}: {field_name}")
            for field_name, old_type in old_fields.items():
                if field_name in new_fields and new_fields[field_name] != old_type:
                    result.diagnostics.add(
                        "error",
                        "ASTRA6004",
                        f"Field type changed in {old_sig.kind} {label}: {field_name} {old_type} -> {new_fields[field_name]}",
                    )
            for field_name in sorted(set(new_fields) - set(old_fields)):
                result.diagnostics.add("warning", "ASTRA6101", f"Field added to {old_sig.kind} {label}: {field_name}")
        elif old_sig.kind == "type":
            if old_sig.target_type != new_sig.target_type:
                result.diagnostics.add(
                    "error",
                    "ASTRA6005",
                    f"Type alias target changed for {label}: {old_sig.target_type} -> {new_sig.target_type}",
                )
        elif old_sig.kind == "query":
            if old_sig.input_type != new_sig.input_type:
                result.diagnostics.add(
                    "error",
                    "ASTRA6006",
                    f"Query input changed for {label}: {old_sig.input_type} -> {new_sig.input_type}",
                )
            if old_sig.output_type != new_sig.output_type:
                result.diagnostics.add(
                    "error",
                    "ASTRA6007",
                    f"Query output changed for {label}: {old_sig.output_type} -> {new_sig.output_type}",
                )
        elif old_sig.kind == "api":
            old_routes = old_sig.routes
            new_routes = new_sig.routes
            for route in sorted(set(old_routes) - set(new_routes)):
                result.diagnostics.add("error", "ASTRA6008", f"API route removed from {label}: {route}")
            for route in sorted(set(new_routes) - set(old_routes)):
                result.diagnostics.add("warning", "ASTRA6102", f"API route added to {label}: {route}")
            for route, old_target in old_routes.items():
                if route in new_routes and new_routes[route] != old_target:
                    result.diagnostics.add(
                        "error",
                        "ASTRA6009",
                        f"API route target changed for {label}: {route} {old_target} -> {new_routes[route]}",
                    )

    for key, sig in cur.items():
        if key not in prev:
            result.diagnostics.add("info", "ASTRA6201", f"New exported artifact added: {sig.module}.{sig.name} ({sig.kind})")

    return result
