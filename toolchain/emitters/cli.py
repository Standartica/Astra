from __future__ import annotations

import json
import sys
from pathlib import Path

from toolchain.compiler.loader import load_modules
from toolchain.emitters.jsonschema import emit_json_schema
from toolchain.emitters.openapi import emit_openapi
from toolchain.emitters.server_fastapi import emit_server_fastapi
from toolchain.emitters.ts_client import emit_ts_client


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m toolchain.emitters.cli <openapi|jsonschema|ts-client|server-fastapi> <file.astra|directory>")
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
    elif kind == "ts-client":
        payload = emit_ts_client(graph)
        print(payload)
        return 0
    elif kind == "server-fastapi":
        payload = emit_server_fastapi(graph)
        print(payload)
        return 0
    else:
        print(f"Unknown emitter kind: {kind}")
        return 3
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
