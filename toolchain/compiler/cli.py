from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from toolchain.compiler.artifact_graph import build_artifact_graph
from toolchain.compiler.binder import bind_module
from toolchain.compiler.compatibility import compare_module_graphs
from toolchain.compiler.effect_analysis import analyze_effects
from toolchain.compiler.loader import load_modules
from toolchain.compiler.semantic_ir import build_semantic_ir
from toolchain.emitters.jsonschema import emit_json_schema
from toolchain.emitters.openapi import emit_openapi
from toolchain.parser.parser import ParseError, parse_source


def _semantic_ir_payload(semantic_ir) -> dict:
    return {
        "modules": {name: asdict(module_ir) for name, module_ir in semantic_ir.modules.items()},
        "diagnostics": [item.to_dict() for item in semantic_ir.diagnostics.items],
    }


def _single_file_payload(path: Path) -> tuple[dict, int]:
    source = path.read_text(encoding="utf-8")
    try:
        module = parse_source(source)
    except ParseError as exc:
        return {"parse_error": str(exc)}, 3
    result = bind_module(module, source=source)
    graph = load_modules(path)
    semantic_ir = build_semantic_ir(graph)
    effect_result = analyze_effects(semantic_ir)
    payload = {
        "mode": "single-file",
        "module": asdict(module),
        "imports": result.imported_modules,
        "symbols": {name: asdict(symbol) for name, symbol in result.symbols.items()},
        "diagnostics": [item.to_dict() for item in result.diagnostics.items],
        "semantic_ir": _semantic_ir_payload(semantic_ir),
        "effects": {
            "summaries": [asdict(item) for item in effect_result.summaries],
            "diagnostics": [item.to_dict() for item in effect_result.diagnostics.items],
        },
        "emitted": {
            "jsonschema": emit_json_schema(graph),
            "openapi": emit_openapi(graph),
        },
    }
    has_errors = result.diagnostics.has_errors() or effect_result.diagnostics.has_errors()
    return payload, (4 if has_errors else 0)


def _multi_module_payload(path: Path) -> tuple[dict, int]:
    module_graph = load_modules(path)
    artifact_graph = build_artifact_graph(module_graph)
    semantic_ir = build_semantic_ir(module_graph, bind_results=artifact_graph.bind_results)
    effect_result = analyze_effects(semantic_ir)
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
        "semantic_ir": _semantic_ir_payload(semantic_ir),
        "effects": {
            "summaries": [asdict(item) for item in effect_result.summaries],
            "diagnostics": [item.to_dict() for item in effect_result.diagnostics.items],
        },
        "emitted": {
            "jsonschema": emit_json_schema(module_graph),
            "openapi": emit_openapi(module_graph),
        },
    }
    has_errors = artifact_graph.diagnostics.has_errors() or effect_result.diagnostics.has_errors()
    return payload, (4 if has_errors else 0)


def _compat_payload(previous: Path, current: Path) -> tuple[dict, int]:
    previous_graph = load_modules(previous)
    current_graph = load_modules(current)
    result = compare_module_graphs(previous_graph, current_graph)
    payload = {
        "mode": "compatibility",
        "previous": str(previous),
        "current": str(current),
        "previous_artifacts": result.previous_count,
        "current_artifacts": result.current_count,
        "diagnostics": [item.to_dict() for item in result.diagnostics.items],
    }
    return payload, (4 if result.diagnostics.has_errors() else 0)


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) == 1:
        path = Path(argv[0])
        if not path.exists():
            print(f"File or directory not found: {path}")
            return 2
        payload, code = _multi_module_payload(path) if path.is_dir() else _single_file_payload(path)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return code
    if len(argv) == 3 and argv[0] == "compat":
        previous = Path(argv[1])
        current = Path(argv[2])
        if not previous.exists() or not current.exists():
            print("Both previous and current paths must exist")
            return 2
        payload, code = _compat_payload(previous, current)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return code
    print("Usage: python -m toolchain.compiler.cli <file.astra|directory>")
    print("   or: python -m toolchain.compiler.cli compat <previous_dir> <current_dir>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
