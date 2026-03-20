from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from toolchain.compiler.diagnostics import DiagnosticBag
from toolchain.parser.ast import Module
from toolchain.parser.parser import ParseError, parse_source


@dataclass(slots=True)
class LoadedModule:
    name: str
    path: str
    source: str
    module: Module


@dataclass(slots=True)
class ModuleGraph:
    root: str
    modules: dict[str, LoadedModule] = field(default_factory=dict)
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)

    def edges(self) -> list[dict[str, str | None]]:
        result: list[dict[str, str | None]] = []
        for module in self.modules.values():
            for imp in module.module.imports:
                result.append({"from": module.name, "to": imp.module_name, "kind": "imports", "alias": imp.alias})
        return result


def _discover_astra_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.rglob("*.astra"))


def load_modules(root_path: str | Path) -> ModuleGraph:
    root = Path(root_path)
    graph = ModuleGraph(root=str(root))
    files = _discover_astra_files(root)
    if not files:
        graph.diagnostics.add("error", "ASTRA4001", f"No .astra files found under '{root}'")
        return graph

    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        try:
            module = parse_source(source)
        except ParseError as exc:
            graph.diagnostics.add("error", "ASTRA4002", f"Parse failed for '{file_path}': {exc}")
            continue

        module_name = module.name or file_path.stem
        if module_name in graph.modules:
            graph.diagnostics.add(
                "error",
                "ASTRA4003",
                f"Duplicate module name '{module_name}' in '{file_path}' and '{graph.modules[module_name].path}'",
                getattr(module.span, "line", None),
                getattr(module.span, "column", None),
            )
            continue

        graph.modules[module_name] = LoadedModule(name=module_name, path=str(file_path), source=source, module=module)

    for loaded in graph.modules.values():
        seen_aliases: set[str] = set()
        for imp in loaded.module.imports:
            if imp.module_name not in graph.modules:
                graph.diagnostics.add(
                    "error",
                    "ASTRA4004",
                    f"Module '{loaded.name}' imports missing module '{imp.module_name}'",
                    getattr(imp.span, "line", None),
                    getattr(imp.span, "column", None),
                )
            alias = imp.alias or imp.module_name
            if alias in seen_aliases:
                graph.diagnostics.add(
                    "error",
                    "ASTRA4005",
                    f"Module '{loaded.name}' imports duplicate alias '{alias}'",
                    getattr(imp.span, "line", None),
                    getattr(imp.span, "column", None),
                )
            seen_aliases.add(alias)
    return graph
