from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable

from toolchain.parser.ast import Module
from .diagnostics import DiagnosticBag

BUILTIN_TYPES = {
    "Int", "Float", "Decimal", "Bool", "String", "Bytes", "Instant", "Duration", "Uuid",
    "Option", "Result", "List", "Set", "Map", "Email", "UserId", "Principal", "TenantId"
}

DECL_ATTRS = {
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


@dataclass(slots=True)
class Symbol:
    name: str
    kind: str
    line: int | None = None
    column: int | None = None
    exported: bool = True


@dataclass(slots=True)
class BindResult:
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)
    imported_modules: list[str] = field(default_factory=list)
    visible_imports: Dict[str, str] = field(default_factory=dict)
    exports: set[str] = field(default_factory=set)


@dataclass(slots=True)
class ExternalModuleSymbols:
    module_name: str
    alias: str | None
    symbols: Dict[str, str]


def _span_snippet(lines: list[str], span) -> str | None:
    if span is None or span.line is None:
        return None
    index = span.line - 1
    if 0 <= index < len(lines):
        return lines[index].rstrip()
    return None


def _split_qualified(name: str) -> tuple[str | None, str]:
    if "." in name:
        left, right = name.rsplit(".", 1)
        return left, right
    return None, name


def _add_symbol(result: BindResult, name: str, kind: str, span, lines: list[str]) -> None:
    if name in result.symbols:
        result.diagnostics.add("error", "ASTRA1001", f"Duplicate declaration for {kind} '{name}'", getattr(span, "line", None), getattr(span, "column", None), _span_snippet(lines, span))
        return
    result.symbols[name] = Symbol(name=name, kind=kind, line=getattr(span, "line", None), column=getattr(span, "column", None))


def bind_module(module: Module, source: str | None = None, external_modules: list[ExternalModuleSymbols] | None = None) -> BindResult:
    result = BindResult()
    lines = (source or "").splitlines()
    module_name = module.name or "<anonymous>"

    for decl in module.imports:
        result.imported_modules.append(decl.module_name)
        alias = decl.alias or decl.module_name
        result.visible_imports[alias] = decl.module_name
        if decl.module_name == module_name:
            result.diagnostics.add("error", "ASTRA1002", f"Module '{module_name}' cannot import itself", decl.span.line if decl.span else None, decl.span.column if decl.span else None, _span_snippet(lines, decl.span))

    for kind, attr in DECL_ATTRS.items():
        for decl in getattr(module, attr):
            _add_symbol(result, decl.name, kind, decl.span, lines)

    external_modules = external_modules or []
    external_by_alias = {ext.alias or ext.module_name: ext for ext in external_modules}

    if module.exports:
        export_names = {decl.name for decl in module.exports}
        for export_decl in module.exports:
            if export_decl.name not in result.symbols:
                result.diagnostics.add("error", "ASTRA1003", f"Export references unknown local symbol '{export_decl.name}'", getattr(export_decl.span, "line", None), getattr(export_decl.span, "column", None), _span_snippet(lines, export_decl.span))
        result.exports = export_names & set(result.symbols.keys())
    else:
        result.exports = set(result.symbols.keys())

    for name, sym in result.symbols.items():
        sym.exported = name in result.exports

    known_local_types = {name for name, sym in result.symbols.items() if sym.kind in {"schema", "enum", "type"}}
    known_exported_external_types = {
        name
        for ext in external_modules
        for name, kind in ext.symbols.items()
        if kind in {"schema", "enum", "type"}
    }
    known_types = set(BUILTIN_TYPES) | known_local_types | known_exported_external_types

    def resolve_symbol(name: str) -> Symbol | None:
        qualifier, bare = _split_qualified(name)
        if qualifier is None:
            local = result.symbols.get(bare)
            if local:
                return local
            matches = []
            for ext in external_modules:
                if bare in ext.symbols:
                    matches.append(Symbol(name=bare, kind=ext.symbols[bare]))
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                result.diagnostics.add("error", "ASTRA5001", f"Ambiguous imported reference '{bare}' in module '{module_name}'")
            return None
        ext = external_by_alias.get(qualifier)
        if ext is None:
            result.diagnostics.add("error", "ASTRA5002", f"Unknown import alias or module '{qualifier}' in qualified reference '{name}'")
            return None
        if bare not in ext.symbols:
            result.diagnostics.add("error", "ASTRA5003", f"Module '{ext.module_name}' does not export symbol '{bare}'")
            return None
        return Symbol(name=name, kind=ext.symbols[bare])

    def require_type(type_name: str, span, owner: str) -> None:
        qualifier, bare = _split_qualified(type_name)
        if qualifier is None and bare in known_types:
            return
        symbol = resolve_symbol(type_name)
        if symbol is None or symbol.kind not in {"schema", "enum", "type"}:
            result.diagnostics.add("error", "ASTRA2001", f"Unknown type '{type_name}' referenced from {owner}", getattr(span, "line", None), getattr(span, "column", None), _span_snippet(lines, span))

    def require_symbol(name: str, expected_kinds: Iterable[str], code_unknown: str, code_mismatch: str, context: str, span) -> None:
        sym = resolve_symbol(name)
        if sym is None:
            result.diagnostics.add("error", code_unknown, f"Unknown {context} '{name}'", getattr(span, "line", None), getattr(span, "column", None), _span_snippet(lines, span))
            return
        if sym.kind not in set(expected_kinds):
            result.diagnostics.add("error", code_mismatch, f"{context.capitalize()} '{name}' has invalid kind '{sym.kind}'", getattr(span, "line", None), getattr(span, "column", None), _span_snippet(lines, span))

    for decl in module.type_aliases:
        require_type(decl.target_type, decl.span, f"type {decl.name}")
    for decl in module.schemas:
        for field in decl.fields:
            require_type(field.type_name, field.span, f"schema {decl.name}")
    for decl in module.commands:
        for field in decl.fields:
            require_type(field.type_name, field.span, f"command {decl.name}")
    for decl in module.events:
        for field in decl.fields:
            require_type(field.type_name, field.span, f"event {decl.name}")
    for decl in module.queries:
        if decl.input_type:
            require_type(decl.input_type, decl.span, f"query {decl.name} input")
        if decl.output_type:
            require_type(decl.output_type, decl.span, f"query {decl.name} output")
        if decl.authorize_policy:
            require_symbol(decl.authorize_policy, {"policy"}, "ASTRA2006", "ASTRA2007", "policy", decl.span)
    for decl in module.policies:
        for param in decl.parameters:
            require_type(param.type_name, param.span, f"policy {decl.name}")
    for decl in module.workflows:
        for param in decl.parameters:
            require_type(param.type_name, param.span, f"workflow {decl.name}")
    for decl in module.functions:
        for param in decl.parameters:
            require_type(param.type_name, param.span, f"fn {decl.name}")
        if decl.return_type:
            require_type(decl.return_type, decl.span, f"fn {decl.name} return")
    for decl in module.invariants:
        for param in decl.parameters:
            require_type(param.type_name, param.span, f"invariant {decl.name}")
    for decl in module.handles:
        require_symbol(decl.command_name, {"command"}, "ASTRA2002", "ASTRA2003", "command", decl.span)
        if decl.event_name:
            require_symbol(decl.event_name, {"event"}, "ASTRA2004", "ASTRA2005", "event", decl.span)
    for api in module.apis:
        seen_routes: set[tuple[str, str]] = set()
        for route in api.routes:
            key = (route.method.lower(), route.path)
            if key in seen_routes:
                result.diagnostics.add("error", "ASTRA3001", f"Duplicate route '{route.method.upper()} {route.path}' in api {api.name}", route.span.line if route.span else None, route.span.column if route.span else None, _span_snippet(lines, route.span))
            seen_routes.add(key)
            sym = resolve_symbol(route.target)
            if sym is None:
                result.diagnostics.add("error", "ASTRA3002", f"Unknown api target '{route.target}' in api {api.name}", route.span.line if route.span else None, route.span.column if route.span else None, _span_snippet(lines, route.span))
            elif sym.kind not in {"command", "query"}:
                result.diagnostics.add("error", "ASTRA3003", f"Api target '{route.target}' must be command or query, got {sym.kind}", route.span.line if route.span else None, route.span.column if route.span else None, _span_snippet(lines, route.span))
    return result
