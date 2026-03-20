from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from .parser import parse_source


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m toolchain.parser.cli <file.astra>")
        return 1

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    source = path.read_text(encoding="utf-8")
    module = parse_source(source)
    print(json.dumps(asdict(module), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
