from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .ast import (
    CapabilityDecl,
    CommandDecl,
    EnumDecl,
    EventDecl,
    FieldDecl,
    FunctionDecl,
    HandleDecl,
    Module,
    ParameterDecl,
    PolicyDecl,
    QueryDecl,
    SchemaDecl,
    SourceSpan,
    WorkflowDecl,
    WorkflowStep,
)
from .tokenizer import Token, tokenize


class ParseError(SyntaxError):
    pass


@dataclass
class Parser:
    tokens: List[Token]
    index: int = 0

    @classmethod
    def from_source(cls, source: str) -> "Parser":
        return cls(list(tokenize(source)))

    def current(self) -> Token:
        return self.tokens[self.index]

    def advance(self) -> Token:
        token = self.current()
        self.index += 1
        return token

    def match(self, kind: str) -> Token | None:
        if self.current().kind == kind:
            return self.advance()
        return None

    def expect(self, kind: str, message: str | None = None) -> Token:
        token = self.current()
        if token.kind != kind:
            detail = message or f"Expected {kind}, got {token.kind} ({token.value!r})"
            raise ParseError(f"{detail} at {token.line}:{token.column}")
        return self.advance()

    def span_from(self, start: Token, end: Token | None = None) -> SourceSpan:
        end = end or start
        return SourceSpan(start.line, start.column, end.line, end.column)

    def parse(self) -> Module:
        module = Module()
        if self.current().kind == "MODULE":
            start = self.advance()
            name_tok = self.expect("IDENT")
            module.name = name_tok.value
            module.span = self.span_from(start, name_tok)

        while self.current().kind != "EOF":
            kind = self.current().kind
            if kind == "SCHEMA":
                module.schemas.append(self.parse_field_block(SchemaDecl))
            elif kind == "COMMAND":
                module.commands.append(self.parse_field_block(CommandDecl))
            elif kind == "EVENT":
                module.events.append(self.parse_field_block(EventDecl))
            elif kind == "QUERY":
                module.queries.append(self.parse_query())
            elif kind == "ENUM":
                module.enums.append(self.parse_enum())
            elif kind == "CAPABILITY":
                module.capabilities.append(self.parse_capability())
            elif kind == "POLICY":
                module.policies.append(self.parse_policy())
            elif kind == "WORKFLOW":
                module.workflows.append(self.parse_workflow())
            elif kind == "HANDLE":
                module.handles.append(self.parse_handle())
            elif kind == "FN":
                module.functions.append(self.parse_function())
            else:
                token = self.current()
                raise ParseError(f"Unexpected token {token.kind} ({token.value!r}) at {token.line}:{token.column}")

        return module

    def parse_identifier_or_path(self) -> str:
        return self.expect("IDENT").value

    def parse_parameters(self) -> List[ParameterDecl]:
        params: List[ParameterDecl] = []
        self.expect("LPAREN")
        while self.current().kind != "RPAREN":
            start = self.current()
            name = self.expect("IDENT").value
            self.expect("COLON")
            type_name = self.parse_identifier_or_path()
            params.append(ParameterDecl(name=name, type_name=type_name, span=self.span_from(start, self.tokens[self.index - 1])))
            if not self.match("COMMA"):
                break
        self.expect("RPAREN")
        return params

    def parse_field_block(self, decl_type):
        start = self.advance()
        name_tok = self.expect("IDENT")
        self.expect("LBRACE")
        fields: List[FieldDecl] = []
        while self.current().kind != "RBRACE":
            field_start = self.current()
            field_name = self.expect("IDENT").value
            self.expect("COLON")
            type_name = self.parse_identifier_or_path()
            fields.append(FieldDecl(field_name, type_name, self.span_from(field_start, self.tokens[self.index - 1])))
        end = self.expect("RBRACE")
        return decl_type(name=name_tok.value, fields=fields, span=self.span_from(start, end))

    def parse_query(self) -> QueryDecl:
        start = self.expect("QUERY")
        name_tok = self.expect("IDENT")
        self.expect("LBRACE")
        input_type = None
        output_type = None
        while self.current().kind != "RBRACE":
            key = self.expect("IDENT", "Expected query field name like input or output").value
            self.expect("COLON")
            value = self.parse_identifier_or_path()
            if key == "input":
                input_type = value
            elif key == "output":
                output_type = value
            else:
                raise ParseError(f"Unknown query property {key!r} at {self.current().line}:{self.current().column}")
        end = self.expect("RBRACE")
        return QueryDecl(name=name_tok.value, input_type=input_type, output_type=output_type, span=self.span_from(start, end))

    def parse_enum(self) -> EnumDecl:
        start = self.expect("ENUM")
        name = self.expect("IDENT").value
        self.expect("LBRACE")
        members: List[str] = []
        while self.current().kind != "RBRACE":
            members.append(self.expect("IDENT").value)
        end = self.expect("RBRACE")
        return EnumDecl(name=name, members=members, span=self.span_from(start, end))

    def parse_capability(self) -> CapabilityDecl:
        start = self.expect("CAPABILITY")
        name = self.expect("IDENT").value
        return CapabilityDecl(name=name, span=self.span_from(start, self.tokens[self.index - 1]))

    def parse_policy(self) -> PolicyDecl:
        start = self.expect("POLICY")
        name = self.expect("IDENT").value
        parameters = self.parse_parameters()
        self.expect("LBRACE")
        requirements: List[str] = []
        while self.current().kind != "RBRACE":
            self.expect("REQUIRE")
            pieces: List[str] = []
            while self.current().kind not in {"REQUIRE", "RBRACE", "EOF"}:
                pieces.append(self.advance().value)
            requirements.append(" ".join(pieces).strip())
        end = self.expect("RBRACE")
        return PolicyDecl(name=name, parameters=parameters, requirements=requirements, span=self.span_from(start, end))

    def parse_workflow(self) -> WorkflowDecl:
        start = self.expect("WORKFLOW")
        name = self.expect("IDENT").value
        parameters = self.parse_parameters()
        deterministic = self.match("DETERMINISTIC") is not None
        self.expect("LBRACE")
        steps: List[WorkflowStep] = []
        while self.current().kind != "RBRACE":
            step_start = self.current()
            self.expect("STEP")
            step_value = self.expect("IDENT").value
            modifier = None
            if self.match("TIMEOUT"):
                modifier = f"timeout {self.expect('IDENT').value}"
            steps.append(WorkflowStep(kind="step", value=step_value, modifier=modifier, span=self.span_from(step_start, self.tokens[self.index - 1])))
        end = self.expect("RBRACE")
        return WorkflowDecl(name=name, parameters=parameters, steps=steps, deterministic=deterministic, span=self.span_from(start, end))

    def parse_effects_list(self) -> List[str]:
        effects: List[str] = []
        self.expect("LBRACKET")
        while self.current().kind != "RBRACKET":
            effects.append(self.expect("IDENT").value)
            if not self.match("COMMA"):
                break
        self.expect("RBRACKET")
        return effects

    def skip_block(self) -> None:
        self.expect("LBRACE")
        depth = 1
        while depth > 0:
            tok = self.advance()
            if tok.kind == "LBRACE":
                depth += 1
            elif tok.kind == "RBRACE":
                depth -= 1
            elif tok.kind == "EOF":
                raise ParseError(f"Unterminated block starting before {tok.line}:{tok.column}")

    def parse_handle(self) -> HandleDecl:
        start = self.expect("HANDLE")
        command_name = self.expect("IDENT").value
        event_name = None
        if self.match("ARROW"):
            event_name = self.expect("IDENT").value
        effects: List[str] = []
        if self.match("WITH"):
            self.expect("EFFECTS")
            effects = self.parse_effects_list()
        if self.current().kind == "LBRACE":
            self.skip_block()
        return HandleDecl(command_name=command_name, event_name=event_name, effects=effects, span=self.span_from(start, self.tokens[self.index - 1]))

    def parse_function(self) -> FunctionDecl:
        start = self.expect("FN")
        name = self.expect("IDENT").value
        parameters = self.parse_parameters()
        return_type = None
        if self.match("ARROW"):
            return_type = self.expect("IDENT").value
        purity = None
        effects: List[str] = []
        if self.match("PURE"):
            purity = "pure"
        elif self.match("EFFECTS"):
            purity = "effectful"
            effects = self.parse_effects_list()
        if self.current().kind == "LBRACE":
            self.skip_block()
        return FunctionDecl(name=name, parameters=parameters, return_type=return_type, purity=purity, effects=effects, span=self.span_from(start, self.tokens[self.index - 1]))


def parse_source(source: str) -> Module:
    return Parser.from_source(source).parse()
