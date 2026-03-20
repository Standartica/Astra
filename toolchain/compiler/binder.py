from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable

from toolchain.parser.ast import Module
from .diagnostics import DiagnosticBag

BUILTIN_TYPES = {
    "Int", "Float", "Decimal", "Bool", "String", "Bytes", "Instant", "Duration", "Uuid",
    "Option", "Result", "List", "Set", "Map", "Email", "UserId", "Principal", "TenantId"
}


@dataclass(slots=True)
class Symbol:
    name: str
    kind: str
    line: int | None = None
    column: int | None = None


@dataclass(slots=True)
class BindResult:
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)
    imported_modules: list[str] = field(default_factory=list)


def _span_snippet(lines: list[str], span) -> str | None:
    if span is None or span.line is None:
        return None
    index = span.line - 1
    if 0 <= index < len(lines):
        return lines[index].rstrip()
    return None


def _add_symbol(result: BindResult, name: str, kind: str, span, lines: list[str]) -> None:
    if name in result.symbols:
        result.diagnostics.add("error", "ASTRA1001", f"Duplicate declaration for {kind} '{name}'", getattr(span, "line", None), getattr(span, "column", None), _span_snippet(lines, span))
        return
    result.symbols[name] = Symbol(name=name, kind=kind, line=getattr(span, "line", None), column=getattr(span, "column", None))


def bind_module(module: Module, source: str | None = None, external_symbols: Dict[str, str] | None = None) -> BindResult:
    result = BindResult()
    lines = (source or "").splitlines()
    module_name = module.name or "<anonymous>"

    for decl in module.imports:
        result.imported_modules.append(decl.module_name)
        if decl.module_name == module_name:
            result.diagnostics.add("error", "ASTRA1002", f"Module '{module_name}' cannot import itself", decl.span.line if decl.span else None, decl.span.column if decl.span else None, _span_snippet(lines, decl.span))

    for decl in module.type_aliases:
        _add_symbol(result, decl.name, "type", decl.span, lines)
    for decl in module.schemas:
        _add_symbol(result, decl.name, "schema", decl.span, lines)
    for decl in module.commands:
        _add_symbol(result, decl.name, "command", decl.span, lines)
    for decl in module.events:
        _add_symbol(result, decl.name, "event", decl.span, lines)
    for decl in module.queries:
        _add_symbol(result, decl.name, "query", decl.span, lines)
    for decl in module.enums:
        _add_symbol(result, decl.name, "enum", decl.span, lines)
    for decl in module.capabilities:
        _add_symbol(result, decl.name, "capability", decl.span, lines)
    for decl in module.policies:
        _add_symbol(result, decl.name, "policy", decl.span, lines)
    for decl in module.workflows:
        _add_symbol(result, decl.name, "workflow", decl.span, lines)
    for decl in module.functions:
        _add_symbol(result, decl.name, "fn", decl.span, lines)
    for decl in module.invariants:
        _add_symbol(result, decl.name, "invariant", decl.span, lines)
    for decl in module.apis:
        _add_symbol(result, decl.name, "api", decl.span, lines)

    external_symbols = external_symbols or {}
    known_types = set(BUILTIN_TYPES) | {name for name, sym in result.symbols.items() if sym.kind in {"schema", "enum", "type"}} | {name for name, kind in external_symbols.items() if kind in {"schema", "enum", "type"}}

    def require_type(type_name: str, span, owner: str) -> None:
        if type_name not in known_types:
            result.diagnostics.add("error", "ASTRA2001", f"Unknown type '{type_name}' referenced from {owner}", getattr(span, "line", None), getattr(span, "column", None), _span_snippet(lines, span))

    def require_symbol(name: str, expected_kinds: Iterable[str], code_unknown: str, code_mismatch: str, context: str, span) -> None:
        sym = result.symbols.get(name)
        if sym is None and name in external_symbols:
            sym = Symbol(name=name, kind=external_symbols[name])
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
            target_sym = result.symbols.get(route.target)
            if target_sym is None:
                result.diagnostics.add("error", "ASTRA3002", f"Unknown api target '{route.target}' in api {api.name}", route.span.line if route.span else None, route.span.column if route.span else None, _span_snippet(lines, route.span))
            elif target_sym.kind not in {"command", "query"}:
                result.diagnostics.add("error", "ASTRA3003", f"Api target '{route.target}' must be command or query, got {target_sym.kind}", route.span.line if route.span else None, route.span.column if route.span else None, _span_snippet(lines, route.span))
    return result
