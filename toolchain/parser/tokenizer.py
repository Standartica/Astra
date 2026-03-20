from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


@dataclass(slots=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


KEYWORDS = {
    "module",
    "schema",
    "command",
    "event",
    "query",
    "enum",
    "capability",
    "policy",
    "require",
    "workflow",
    "step",
    "timeout",
    "deterministic",
    "handle",
    "with",
    "effects",
    "fn",
    "pure",
}
SINGLE_CHAR = {
    "{": "LBRACE",
    "}": "RBRACE",
    ":": "COLON",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    ",": "COMMA",
}
DOUBLE_CHAR = {"->": "ARROW"}


def tokenize(source: str) -> Iterator[Token]:
    line = 1
    col = 1
    i = 0
    n = len(source)

    while i < n:
        ch = source[i]

        if ch in " \t\r":
            i += 1
            col += 1
            continue

        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue

        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            while i < n and source[i] != "\n":
                i += 1
                col += 1
            continue

        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            i += 2
            col += 2
            while i + 1 < n and not (source[i] == "*" and source[i + 1] == "/"):
                if source[i] == "\n":
                    line += 1
                    col = 1
                    i += 1
                else:
                    i += 1
                    col += 1
            if i + 1 >= n:
                raise SyntaxError(f"Unterminated block comment at {line}:{col}")
            i += 2
            col += 2
            continue

        if i + 1 < n and source[i : i + 2] in DOUBLE_CHAR:
            value = source[i : i + 2]
            yield Token(DOUBLE_CHAR[value], value, line, col)
            i += 2
            col += 2
            continue

        if ch in SINGLE_CHAR:
            yield Token(SINGLE_CHAR[ch], ch, line, col)
            i += 1
            col += 1
            continue

        if ch.isalpha() or ch == "_":
            start = i
            start_col = col
            while i < n and (source[i].isalnum() or source[i] in "_-."):
                i += 1
                col += 1
            value = source[start:i]
            kind = value.upper() if value in KEYWORDS else "IDENT"
            yield Token(kind, value, line, start_col)
            continue

        raise SyntaxError(f"Unexpected character {ch!r} at {line}:{col}")

    yield Token("EOF", "", line, col)
