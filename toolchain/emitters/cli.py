from __future__ import annotations

import json
import sys
from pathlib import Path

from toolchain.compiler.loader import load_modules
from toolchain.emitters.jsonschema import emit_json_schema
from toolchain.emitters.openapi import emit_openapi


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m toolchain.emitters.cli <openapi|jsonschema> <file.astra|directory>")
        return 1
    kind = sys.argv[1].lower()
    path = Path(sys.argv[2])
    if not path.exists():
        print(f"File or directory not found: {path}")
        return 2
    graph = load_modules(path)
    if kind == "openapi":
        payload = emit_openapi(graph)
    elif kind == "jsonschema":
        payload = emit_json_schema(graph)
    else:
        print(f"Unknown emitter kind: {kind}")
        return 3
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
