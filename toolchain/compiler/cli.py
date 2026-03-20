from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from toolchain.compiler.artifact_graph import build_artifact_graph
from toolchain.compiler.loader import load_modules
from toolchain.parser.parser import ParseError, parse_source
from toolchain.compiler.binder import bind_module


def _single_file_payload(path: Path) -> tuple[dict, int]:
    source = path.read_text(encoding="utf-8")
    try:
        module = parse_source(source)
    except ParseError as exc:
        return {"parse_error": str(exc)}, 3
    result = bind_module(module, source=source)
    payload = {
        "mode": "single-file",
        "module": asdict(module),
        "imports": result.imported_modules,
        "symbols": {name: asdict(symbol) for name, symbol in result.symbols.items()},
        "diagnostics": [item.to_dict() for item in result.diagnostics.items],
    }
    return payload, (4 if result.diagnostics.has_errors() else 0)


def _multi_module_payload(path: Path) -> tuple[dict, int]:
    module_graph = load_modules(path)
    artifact_graph = build_artifact_graph(module_graph)
    artifact_graph.diagnostics.extend(module_graph.diagnostics.items)
    payload = {
        "mode": "module-graph",
        "root": str(path),
        "modules": {
            name: {
                "path": loaded.path,
                "imports": [imp.module_name for imp in loaded.module.imports],
            }
            for name, loaded in module_graph.modules.items()
        },
        "module_edges": module_graph.edges(),
        "artifact_nodes": [asdict(node) for node in artifact_graph.nodes],
        "artifact_edges": [asdict(edge) for edge in artifact_graph.edges],
        "symbols": {
            module_name: {name: asdict(symbol) for name, symbol in bind_result.symbols.items()}
            for module_name, bind_result in artifact_graph.bind_results.items()
        },
        "diagnostics": [item.to_dict() for item in artifact_graph.diagnostics.items],
    }
    return payload, (4 if artifact_graph.diagnostics.has_errors() else 0)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m toolchain.compiler.cli <file.astra | directory>")
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File or directory not found: {path}")
        return 2
    if path.is_dir():
        payload, code = _multi_module_payload(path)
    else:
        payload, code = _single_file_payload(path)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
