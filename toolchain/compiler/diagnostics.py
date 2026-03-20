from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(slots=True)
class Diagnostic:
    level: str
    code: str
    message: str
    line: int | None = None
    column: int | None = None
    snippet: str | None = None

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "snippet": self.snippet,
        }


class DiagnosticBag:
    def __init__(self) -> None:
        self.items: List[Diagnostic] = []

    def add(self, level: str, code: str, message: str, line: int | None = None, column: int | None = None, snippet: str | None = None) -> None:
        self.items.append(Diagnostic(level=level, code=code, message=message, line=line, column=column, snippet=snippet))

    def extend(self, values: Iterable[Diagnostic]) -> None:
        self.items.extend(values)

    def has_errors(self) -> bool:
        return any(item.level == "error" for item in self.items)
