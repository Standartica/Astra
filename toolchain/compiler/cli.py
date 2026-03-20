from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from toolchain.compiler.binder import bind_module
from toolchain.parser.parser import ParseError, parse_source


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m toolchain.compiler.cli <file.astra>")
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2
    source = path.read_text(encoding="utf-8")
    try:
        module = parse_source(source)
    except ParseError as exc:
        print(json.dumps({"parse_error": str(exc)}, indent=2, ensure_ascii=False))
        return 3
    result = bind_module(module, source=source)
    payload = {
        "module": asdict(module),
        "imports": result.imported_modules,
        "symbols": {name: asdict(symbol) for name, symbol in result.symbols.items()},
        "diagnostics": [item.to_dict() for item in result.diagnostics.items],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 4 if result.diagnostics.has_errors() else 0


if __name__ == "__main__":
    raise SystemExit(main())
