from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from toolchain.parser.ast import Module
from .diagnostics import DiagnosticBag

BUILTIN_TYPES = {
    "Int", "Float", "Decimal", "Bool", "String", "Bytes", "Instant", "Duration", "Uuid",
    "Option", "Result", "List", "Set", "Map"
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


def _add_symbol(result: BindResult, name: str, kind: str, span) -> None:
    if name in result.symbols:
        result.diagnostics.add(
            "error",
            "ASTRA1001",
            f"Duplicate declaration for {kind} '{name}'",
            getattr(span, "line", None),
            getattr(span, "column", None),
        )
        return
    result.symbols[name] = Symbol(name=name, kind=kind, line=getattr(span, "line", None), column=getattr(span, "column", None))


def bind_module(module: Module) -> BindResult:
    result = BindResult()

    for decl in module.schemas:
        _add_symbol(result, decl.name, "schema", decl.span)
    for decl in module.commands:
        _add_symbol(result, decl.name, "command", decl.span)
    for decl in module.events:
        _add_symbol(result, decl.name, "event", decl.span)
    for decl in module.queries:
        _add_symbol(result, decl.name, "query", decl.span)
    for decl in module.enums:
        _add_symbol(result, decl.name, "enum", decl.span)
    for decl in module.capabilities:
        _add_symbol(result, decl.name, "capability", decl.span)
    for decl in module.policies:
        _add_symbol(result, decl.name, "policy", decl.span)
    for decl in module.workflows:
        _add_symbol(result, decl.name, "workflow", decl.span)
    for decl in module.functions:
        _add_symbol(result, decl.name, "fn", decl.span)

    known_types = set(BUILTIN_TYPES) | {name for name, sym in result.symbols.items() if sym.kind in {"schema", "enum"}}

    def require_type(type_name: str, span, owner: str) -> None:
        if type_name not in known_types:
            result.diagnostics.add(
                "error",
                "ASTRA2001",
                f"Unknown type '{type_name}' referenced from {owner}",
                getattr(span, "line", None),
                getattr(span, "column", None),
            )

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
    for decl in module.handles:
        if decl.command_name not in result.symbols:
            result.diagnostics.add("error", "ASTRA2002", f"Unknown command '{decl.command_name}' in handle", decl.span.line if decl.span else None, decl.span.column if decl.span else None)
        elif result.symbols[decl.command_name].kind != "command":
            result.diagnostics.add("error", "ASTRA2003", f"Handle target '{decl.command_name}' is not a command", decl.span.line if decl.span else None, decl.span.column if decl.span else None)
        if decl.event_name:
            sym = result.symbols.get(decl.event_name)
            if sym is None:
                result.diagnostics.add("error", "ASTRA2004", f"Unknown event '{decl.event_name}' in handle", decl.span.line if decl.span else None, decl.span.column if decl.span else None)
            elif sym.kind != "event":
                result.diagnostics.add("error", "ASTRA2005", f"Handle result '{decl.event_name}' is not an event", decl.span.line if decl.span else None, decl.span.column if decl.span else None)

    return result
