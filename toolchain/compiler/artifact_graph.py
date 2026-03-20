from __future__ import annotations

from dataclasses import dataclass, field

from toolchain.compiler.binder import DECL_ATTRS, BindResult, ExternalModuleSymbols, bind_module
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
    exported: bool = True


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


def _node_id(module_name: str, kind: str, name: str) -> str:
    return f"{module_name}:{kind}:{name}"


def _split_qualified(name: str) -> tuple[str | None, str]:
    if "." in name:
        left, right = name.rsplit(".", 1)
        return left, right
    return None, name


def _exported_symbol_maps(module_graph: ModuleGraph) -> dict[str, dict[str, str]]:
    exported: dict[str, dict[str, str]] = {}
    for module_name, loaded in module_graph.modules.items():
        local_symbols: dict[str, str] = {}
        for kind, attr in DECL_ATTRS.items():
            for decl in getattr(loaded.module, attr):
                local_symbols[decl.name] = kind
        if loaded.module.exports:
            exported[module_name] = {name: local_symbols[name] for name in {e.name for e in loaded.module.exports} if name in local_symbols}
        else:
            exported[module_name] = local_symbols
    return exported


def build_artifact_graph(module_graph: ModuleGraph) -> ArtifactGraphResult:
    result = ArtifactGraphResult()
    if module_graph.diagnostics.items:
        result.diagnostics.extend(module_graph.diagnostics.items)

    exported_maps = _exported_symbol_maps(module_graph)
    symbol_index: dict[tuple[str, str], ArtifactNode] = {}

    for module_name, loaded in module_graph.modules.items():
        external_modules: list[ExternalModuleSymbols] = []
        for imp in loaded.module.imports:
            imported_loaded = module_graph.modules.get(imp.module_name)
            if imported_loaded is None:
                continue
            external_modules.append(ExternalModuleSymbols(module_name=imp.module_name, alias=imp.alias, symbols=exported_maps[imp.module_name]))

        bind_result = bind_module(loaded.module, source=loaded.source, external_modules=external_modules)
        result.bind_results[module_name] = bind_result
        result.diagnostics.extend(bind_result.diagnostics.items)

        for kind, attr in DECL_ATTRS.items():
            for decl in getattr(loaded.module, attr):
                node = ArtifactNode(
                    id=_node_id(module_name, kind, decl.name),
                    module=module_name,
                    name=decl.name,
                    kind=kind,
                    path=loaded.path,
                    line=getattr(decl.span, "line", None),
                    column=getattr(decl.span, "column", None),
                    exported=(decl.name in bind_result.exports),
                )
                result.nodes.append(node)
                symbol_index[(module_name, decl.name)] = node

    for module_name, loaded in module_graph.modules.items():
        for imp in loaded.module.imports:
            if imp.module_name in module_graph.modules:
                result.edges.append(ArtifactEdge(from_id=f"module:{module_name}", to_id=f"module:{imp.module_name}", kind=f"imports:{imp.alias or imp.module_name}"))

    def resolve_reference(current_module: str, name: str, allowed_kinds: set[str]) -> ArtifactNode | None:
        qualifier, bare = _split_qualified(name)
        if qualifier is None:
            local = symbol_index.get((current_module, bare))
            if local and local.kind in allowed_kinds:
                return local
            imported_names = []
            for imp in module_graph.modules[current_module].module.imports:
                if bare in exported_maps.get(imp.module_name, {}):
                    imported_names.append(imp.module_name)
            matches = [symbol_index[(mod_name, bare)] for mod_name in imported_names if (mod_name, bare) in symbol_index and symbol_index[(mod_name, bare)].kind in allowed_kinds]
            if len(matches) == 1:
                return matches[0]
            return None

        target_module = None
        for imp in module_graph.modules[current_module].module.imports:
            if qualifier in {imp.alias, imp.module_name}:
                target_module = imp.module_name
                break
        if target_module is None:
            return None
        node = symbol_index.get((target_module, bare))
        if node and node.exported and node.kind in allowed_kinds:
            return node
        return None

    for module_name, loaded in module_graph.modules.items():
        for query in loaded.module.queries:
            if query.authorize_policy:
                target = resolve_reference(module_name, query.authorize_policy, {"policy"})
                if target:
                    result.edges.append(ArtifactEdge(_node_id(module_name, "query", query.name), target.id, "authorizes-with"))

        for handle in loaded.module.handles:
            handle_id = f"{module_name}:handle:{handle.command_name}->{handle.event_name or '_'}"
            cmd = resolve_reference(module_name, handle.command_name, {"command"})
            if cmd:
                result.edges.append(ArtifactEdge(handle_id, cmd.id, "handles"))
            if handle.event_name:
                evt = resolve_reference(module_name, handle.event_name, {"event"})
                if evt:
                    result.edges.append(ArtifactEdge(handle_id, evt.id, "emits"))

        for api in loaded.module.apis:
            api_id = _node_id(module_name, "api", api.name)
            for route in api.routes:
                target = resolve_reference(module_name, route.target, {"command", "query"})
                if target:
                    result.edges.append(ArtifactEdge(api_id, target.id, f"route:{route.method.lower()} {route.path}"))

    return result
