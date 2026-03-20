from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .ast import CommandDecl, EnumDecl, EventDecl, FieldDecl, Module, QueryDecl, SchemaDecl
from .tokenizer import Token, tokenize


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

    def expect(self, kind: str) -> Token:
        token = self.current()
        if token.kind != kind:
            raise SyntaxError(
                f"Expected {kind}, got {token.kind} ({token.value!r}) at {token.line}:{token.column}"
            )
        return self.advance()

    def parse(self) -> Module:
        module = Module()
        if self.current().kind == "MODULE":
            self.advance()
            module.name = self.expect("IDENT").value

        while self.current().kind != "EOF":
            kind = self.current().kind
            if kind == "SCHEMA":
                module.schemas.append(self.parse_field_block(SchemaDecl))
            elif kind == "COMMAND":
                module.commands.append(self.parse_field_block(CommandDecl))
            elif kind == "EVENT":
                module.events.append(self.parse_field_block(EventDecl))
            elif kind == "QUERY":
                module.queries.append(self.parse_field_block(QueryDecl))
            elif kind == "ENUM":
                module.enums.append(self.parse_enum())
            else:
                token = self.current()
                raise SyntaxError(f"Unexpected token {token.kind} ({token.value!r}) at {token.line}:{token.column}")

        return module

    def parse_field_block(self, decl_type):
        self.advance()
        name = self.expect("IDENT").value
        self.expect("LBRACE")
        fields: List[FieldDecl] = []
        while self.current().kind != "RBRACE":
            field_name = self.expect("IDENT").value
            self.expect("COLON")
            type_name = self.expect("IDENT").value
            fields.append(FieldDecl(field_name, type_name))
        self.expect("RBRACE")
        return decl_type(name=name, fields=fields)

    def parse_enum(self) -> EnumDecl:
        self.expect("ENUM")
        name = self.expect("IDENT").value
        self.expect("LBRACE")
        members: List[str] = []
        while self.current().kind != "RBRACE":
            members.append(self.expect("IDENT").value)
        self.expect("RBRACE")
        return EnumDecl(name=name, members=members)


def parse_source(source: str) -> Module:
    return Parser.from_source(source).parse()
