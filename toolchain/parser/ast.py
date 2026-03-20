from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class FieldDecl:
    name: str
    type_name: str


@dataclass(slots=True)
class SchemaDecl:
    name: str
    fields: List[FieldDecl] = field(default_factory=list)


@dataclass(slots=True)
class CommandDecl:
    name: str
    fields: List[FieldDecl] = field(default_factory=list)


@dataclass(slots=True)
class EventDecl:
    name: str
    fields: List[FieldDecl] = field(default_factory=list)


@dataclass(slots=True)
class QueryDecl:
    name: str
    fields: List[FieldDecl] = field(default_factory=list)


@dataclass(slots=True)
class EnumDecl:
    name: str
    members: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Module:
    name: Optional[str] = None
    schemas: List[SchemaDecl] = field(default_factory=list)
    commands: List[CommandDecl] = field(default_factory=list)
    events: List[EventDecl] = field(default_factory=list)
    queries: List[QueryDecl] = field(default_factory=list)
    enums: List[EnumDecl] = field(default_factory=list)
