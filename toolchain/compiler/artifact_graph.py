from __future__ import annotations

from dataclasses import dataclass, field

from toolchain.compiler.binder import BindResult, bind_module
from toolchain.compiler.diagnostics import DiagnosticBag
from toolchain.compiler.loader import ModuleGraph


@dataclass(slots=True)
class ArtifactNode:
    id: str
    module: str
    name: str
    kind: str
    path: str
    line: int | None = None
    column: int | None = None


@dataclass(slots=True)
class ArtifactEdge:
    from_id: str
    to_id: str
    kind: str


@dataclass(slots=True)
class ArtifactGraphResult:
    bind_results: dict[str, BindResult] = field(default_factory=dict)
    nodes: list[ArtifactNode] = field(default_factory=list)
    edges: list[ArtifactEdge] = field(default_factory=list)
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)


DECL_GROUPS = {
    "type": "type_aliases",
    "schema": "schemas",
    "command": "commands",
    "event": "events",
    "query": "queries",
    "enum": "enums",
    "capability": "capabilities",
    "policy": "policies",
    "workflow": "workflows",
    "fn": "functions",
    "invariant": "invariants",
    "api": "apis",
}


def _node_id(module_name: str, kind: str, name: str) -> str:
    return f"{module_name}:{kind}:{name}"


def build_artifact_graph(module_graph: ModuleGraph) -> ArtifactGraphResult:
    result = ArtifactGraphResult()
    symbol_index: dict[tuple[str, str], ArtifactNode] = {}

    external_index: dict[str, dict[str, str]] = {}
    for module_name, loaded in module_graph.modules.items():
        imported_modules = [imp.module_name for imp in loaded.module.imports]
        external_symbols: dict[str, str] = {}
        for imported_module in imported_modules:
            imported_loaded = module_graph.modules.get(imported_module)
            if not imported_loaded:
                continue
            for kind, attr in DECL_GROUPS.items():
                for decl in getattr(imported_loaded.module, attr):
                    external_symbols.setdefault(decl.name, kind)
        external_index[module_name] = external_symbols

    # bind per module
    for module_name, loaded in module_graph.modules.items():
        bind_result = bind_module(loaded.module, source=loaded.source, external_symbols=external_index[module_name])
        result.bind_results[module_name] = bind_result
        result.diagnostics.extend(bind_result.diagnostics.items)

        for kind, attr in DECL_GROUPS.items():
            for decl in getattr(loaded.module, attr):
                node = ArtifactNode(
                    id=_node_id(module_name, kind, decl.name),
                    module=module_name,
                    name=decl.name,
                    kind=kind,
                    path=loaded.path,
                    line=getattr(decl.span, "line", None),
                    column=getattr(decl.span, "column", None),
                )
                result.nodes.append(node)
                symbol_index[(module_name, decl.name)] = node

    # module import edges
    for module_name, loaded in module_graph.modules.items():
        for imp in loaded.module.imports:
            if imp.module_name in module_graph.modules:
                result.edges.append(
                    ArtifactEdge(
                        from_id=f"module:{module_name}",
                        to_id=f"module:{imp.module_name}",
                        kind="imports",
                    )
                )

    # cross-module reference helpers
    def resolve_reference(current_module: str, name: str, allowed_kinds: set[str]) -> ArtifactNode | None:
        local = symbol_index.get((current_module, name))
        if local and local.kind in allowed_kinds:
            return local
        imported_names = [imp.module_name for imp in module_graph.modules[current_module].module.imports]
        matches = [symbol_index[(mod_name, name)] for mod_name in imported_names if (mod_name, name) in symbol_index and symbol_index[(mod_name, name)].kind in allowed_kinds]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            loaded = module_graph.modules[current_module]
            result.diagnostics.add(
                "error",
                "ASTRA5001",
                f"Ambiguous reference '{name}' in module '{current_module}'",
                snippet=loaded.path,
            )
        return None

    for module_name, loaded in module_graph.modules.items():
        # query policy edges
        for query in loaded.module.queries:
            if query.authorize_policy:
                target = resolve_reference(module_name, query.authorize_policy, {"policy"})
                if target:
                    result.edges.append(ArtifactEdge(_node_id(module_name, "query", query.name), target.id, "authorizes-with"))

        # handle edges
        for handle in loaded.module.handles:
            cmd = resolve_reference(module_name, handle.command_name, {"command"})
            if cmd:
                result.edges.append(ArtifactEdge(f"{module_name}:handle:{handle.command_name}->{handle.event_name or '_'}", cmd.id, "handles"))
            if handle.event_name:
                evt = resolve_reference(module_name, handle.event_name, {"event"})
                if evt:
                    result.edges.append(ArtifactEdge(f"{module_name}:handle:{handle.command_name}->{handle.event_name}", evt.id, "emits"))

        # api route edges
        for api in loaded.module.apis:
            api_id = _node_id(module_name, "api", api.name)
            for route in api.routes:
                target = resolve_reference(module_name, route.target, {"command", "query"})
                if target:
                    result.edges.append(ArtifactEdge(api_id, target.id, f"route:{route.method.lower()} {route.path}"))

    return result
