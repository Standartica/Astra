from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class SourceSpan:
    line: int
    column: int
    end_line: int | None = None
    end_column: int | None = None


@dataclass(slots=True)
class FieldDecl:
    name: str
    type_name: str
    span: SourceSpan | None = None


@dataclass(slots=True)
class ParameterDecl:
    name: str
    type_name: str
    span: SourceSpan | None = None


@dataclass(slots=True)
class SchemaDecl:
    name: str
    fields: List[FieldDecl] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass(slots=True)
class CommandDecl:
    name: str
    fields: List[FieldDecl] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass(slots=True)
class EventDecl:
    name: str
    fields: List[FieldDecl] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass(slots=True)
class QueryDecl:
    name: str
    input_type: Optional[str] = None
    output_type: Optional[str] = None
    span: SourceSpan | None = None


@dataclass(slots=True)
class EnumDecl:
    name: str
    members: List[str] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass(slots=True)
class CapabilityDecl:
    name: str
    span: SourceSpan | None = None


@dataclass(slots=True)
class PolicyDecl:
    name: str
    parameters: List[ParameterDecl] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass(slots=True)
class WorkflowStep:
    kind: str
    value: str
    modifier: Optional[str] = None
    span: SourceSpan | None = None


@dataclass(slots=True)
class WorkflowDecl:
    name: str
    parameters: List[ParameterDecl] = field(default_factory=list)
    steps: List[WorkflowStep] = field(default_factory=list)
    deterministic: bool = False
    span: SourceSpan | None = None


@dataclass(slots=True)
class HandleDecl:
    command_name: str
    event_name: Optional[str] = None
    effects: List[str] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass(slots=True)
class FunctionDecl:
    name: str
    parameters: List[ParameterDecl] = field(default_factory=list)
    return_type: Optional[str] = None
    purity: Optional[str] = None
    effects: List[str] = field(default_factory=list)
    span: SourceSpan | None = None


@dataclass(slots=True)
class Module:
    name: Optional[str] = None
    schemas: List[SchemaDecl] = field(default_factory=list)
    commands: List[CommandDecl] = field(default_factory=list)
    events: List[EventDecl] = field(default_factory=list)
    queries: List[QueryDecl] = field(default_factory=list)
    enums: List[EnumDecl] = field(default_factory=list)
    capabilities: List[CapabilityDecl] = field(default_factory=list)
    policies: List[PolicyDecl] = field(default_factory=list)
    workflows: List[WorkflowDecl] = field(default_factory=list)
    handles: List[HandleDecl] = field(default_factory=list)
    functions: List[FunctionDecl] = field(default_factory=list)
    span: SourceSpan | None = None
