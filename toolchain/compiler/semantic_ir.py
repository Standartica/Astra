from __future__ import annotations

from dataclasses import dataclass, field

from toolchain.compiler.artifact_graph import _exported_symbol_maps
from toolchain.compiler.binder import BUILTIN_TYPES
from toolchain.compiler.diagnostics import DiagnosticBag
from toolchain.compiler.loader import ModuleGraph


@dataclass(slots=True)
class TypeRef:
    name: str
    module: str | None
    kind: str
    qualified_name: str
    builtin: bool = False


@dataclass(slots=True)
class ParameterIR:
    name: str
    type_ref: TypeRef


@dataclass(slots=True)
class FieldIR:
    name: str
    type_ref: TypeRef


@dataclass(slots=True)
class TypeAliasIR:
    name: str
    target: TypeRef


@dataclass(slots=True)
class SchemaIR:
    name: str
    fields: list[FieldIR] = field(default_factory=list)


@dataclass(slots=True)
class CommandIR:
    name: str
    fields: list[FieldIR] = field(default_factory=list)


@dataclass(slots=True)
class EventIR:
    name: str
    fields: list[FieldIR] = field(default_factory=list)


@dataclass(slots=True)
class QueryIR:
    name: str
    input_type: TypeRef | None = None
    output_type: TypeRef | None = None
    authorize_policy: str | None = None


@dataclass(slots=True)
class FunctionIR:
    name: str
    parameters: list[ParameterIR] = field(default_factory=list)
    return_type: TypeRef | None = None
    purity: str | None = None
    effects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class HandleIR:
    command: str
    event: str | None = None
    effects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkflowStepIR:
    kind: str
    value: str
    modifier: str | None = None
    resolved_kind: str | None = None
    resolved_qualified_name: str | None = None


@dataclass(slots=True)
class WorkflowIR:
    name: str
    parameters: list[ParameterIR] = field(default_factory=list)
    steps: list[WorkflowStepIR] = field(default_factory=list)
    deterministic: bool = False


@dataclass(slots=True)
class ApiRouteIR:
    method: str
    path: str
    target_kind: str | None
    target: str


@dataclass(slots=True)
class ApiIR:
    name: str
    routes: list[ApiRouteIR] = field(default_factory=list)


@dataclass(slots=True)
class ModuleIR:
    name: str
    exports: list[str] = field(default_factory=list)
    type_aliases: list[TypeAliasIR] = field(default_factory=list)
    schemas: list[SchemaIR] = field(default_factory=list)
    commands: list[CommandIR] = field(default_factory=list)
    events: list[EventIR] = field(default_factory=list)
    queries: list[QueryIR] = field(default_factory=list)
    functions: list[FunctionIR] = field(default_factory=list)
    handles: list[HandleIR] = field(default_factory=list)
    workflows: list[WorkflowIR] = field(default_factory=list)
    apis: list[ApiIR] = field(default_factory=list)


@dataclass(slots=True)
class SemanticIRResult:
    modules: dict[str, ModuleIR] = field(default_factory=dict)
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)


def _split_qualified(name: str) -> tuple[str | None, str]:
    if "." in name:
        left, right = name.rsplit(".", 1)
        return left, right
    return None, name


def build_semantic_ir(module_graph: ModuleGraph, bind_results: dict[str, object] | None = None) -> SemanticIRResult:
    result = SemanticIRResult()
    result.diagnostics.extend(module_graph.diagnostics.items)
    exported_maps = _exported_symbol_maps(module_graph)

    local_symbols: dict[str, dict[str, str]] = {}
    for module_name, loaded in module_graph.modules.items():
        symbols: dict[str, str] = {}
        for kind, attr in {
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
        }.items():
            for decl in getattr(loaded.module, attr):
                symbols[decl.name] = kind
        local_symbols[module_name] = symbols

    def resolve_name(current_module: str, name: str, allowed_kinds: set[str] | None = None) -> tuple[str | None, str | None]:
        qualifier, bare = _split_qualified(name)
        if qualifier is None:
            local_kind = local_symbols.get(current_module, {}).get(bare)
            if local_kind and (allowed_kinds is None or local_kind in allowed_kinds):
                return current_module, local_kind
            imported = []
            for imp in module_graph.modules[current_module].module.imports:
                exported = exported_maps.get(imp.module_name, {})
                kind = exported.get(bare)
                if kind and (allowed_kinds is None or kind in allowed_kinds):
                    imported.append((imp.module_name, kind))
            if len(imported) == 1:
                return imported[0]
            return None, None
        target_module = None
        for imp in module_graph.modules[current_module].module.imports:
            if qualifier in {imp.alias, imp.module_name}:
                target_module = imp.module_name
                break
        if target_module is None:
            return None, None
        target_kind = exported_maps.get(target_module, {}).get(bare)
        if target_kind is None or (allowed_kinds is not None and target_kind not in allowed_kinds):
            return None, None
        return target_module, target_kind

    def resolve_type_ref(current_module: str, type_name: str) -> TypeRef:
        qualifier, bare = _split_qualified(type_name)
        if qualifier is None and bare in BUILTIN_TYPES:
            return TypeRef(name=bare, module=None, kind="builtin", qualified_name=bare, builtin=True)
        target_module, target_kind = resolve_name(current_module, type_name, {"type", "schema", "enum"})
        if target_module and target_kind:
            _, bare_name = _split_qualified(type_name)
            return TypeRef(name=bare_name, module=target_module, kind=target_kind, qualified_name=f"{target_module}.{bare_name}")
        return TypeRef(name=type_name, module=qualifier, kind="unknown", qualified_name=type_name)

    def resolve_symbol_qn(current_module: str, name: str, allowed_kinds: set[str] | None = None) -> tuple[str | None, str | None, str | None]:
        target_module, target_kind = resolve_name(current_module, name, allowed_kinds)
        if target_module is None or target_kind is None:
            return None, None, None
        _, bare = _split_qualified(name)
        return target_module, target_kind, f"{target_module}.{bare}"

    for module_name, loaded in module_graph.modules.items():
        exports = [decl.name for decl in loaded.module.exports] if loaded.module.exports else sorted(local_symbols[module_name].keys())
        module_ir = ModuleIR(name=module_name, exports=exports)
        for decl in loaded.module.type_aliases:
            module_ir.type_aliases.append(TypeAliasIR(name=decl.name, target=resolve_type_ref(module_name, decl.target_type)))
        for decl in loaded.module.schemas:
            module_ir.schemas.append(SchemaIR(name=decl.name, fields=[FieldIR(name=f.name, type_ref=resolve_type_ref(module_name, f.type_name)) for f in decl.fields]))
        for decl in loaded.module.commands:
            module_ir.commands.append(CommandIR(name=decl.name, fields=[FieldIR(name=f.name, type_ref=resolve_type_ref(module_name, f.type_name)) for f in decl.fields]))
        for decl in loaded.module.events:
            module_ir.events.append(EventIR(name=decl.name, fields=[FieldIR(name=f.name, type_ref=resolve_type_ref(module_name, f.type_name)) for f in decl.fields]))
        for decl in loaded.module.queries:
            module_ir.queries.append(QueryIR(name=decl.name, input_type=resolve_type_ref(module_name, decl.input_type) if decl.input_type else None, output_type=resolve_type_ref(module_name, decl.output_type) if decl.output_type else None, authorize_policy=decl.authorize_policy))
        for decl in loaded.module.functions:
            module_ir.functions.append(FunctionIR(name=decl.name, parameters=[ParameterIR(name=p.name, type_ref=resolve_type_ref(module_name, p.type_name)) for p in decl.parameters], return_type=resolve_type_ref(module_name, decl.return_type) if decl.return_type else None, purity=decl.purity, effects=list(decl.effects)))
        for decl in loaded.module.handles:
            _, _, cmd_qn = resolve_symbol_qn(module_name, decl.command_name, {"command"})
            _, _, event_qn = resolve_symbol_qn(module_name, decl.event_name, {"event"}) if decl.event_name else (None, None, None)
            module_ir.handles.append(HandleIR(command=cmd_qn or decl.command_name, event=event_qn or decl.event_name, effects=list(decl.effects)))
        for decl in loaded.module.workflows:
            steps: list[WorkflowStepIR] = []
            for step in decl.steps:
                _, kind, qn = resolve_symbol_qn(module_name, step.value, {"fn", "command", "query", "workflow"})
                steps.append(WorkflowStepIR(kind=step.kind, value=step.value, modifier=step.modifier, resolved_kind=kind, resolved_qualified_name=qn))
            module_ir.workflows.append(WorkflowIR(name=decl.name, parameters=[ParameterIR(name=p.name, type_ref=resolve_type_ref(module_name, p.type_name)) for p in decl.parameters], steps=steps, deterministic=decl.deterministic))
        for decl in loaded.module.apis:
            routes: list[ApiRouteIR] = []
            for route in decl.routes:
                _, kind, qn = resolve_symbol_qn(module_name, route.target, {"command", "query"})
                routes.append(ApiRouteIR(method=route.method.lower(), path=route.path, target_kind=kind, target=qn or route.target))
            module_ir.apis.append(ApiIR(name=decl.name, routes=routes))
        result.modules[module_name] = module_ir

    return result
