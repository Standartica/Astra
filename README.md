# Astra

Astra is an artifact-first, schema-centric, effect-aware, workflow-native language and toolchain draft for AI-native software development.

## Repository goals

This repository is an early draft of:

- the Astra language vision
- core syntax and semantics
- artifact model
- effect model
- workflow model
- compiler pipeline
- example modules
- a minimal toolchain skeleton

## Current status

This is a draft repository, not a production-ready compiler.

Implemented in this draft:

- documentation for the language direction
- RFC-style design notes
- example `.astra` module
- Python prototype toolchain skeleton:
  - AST model
  - tokenizer
  - minimal parser for a subset of Astra
  - CLI entry point

## Repository layout

```text
Astra/
  README.md
  docs/
  specs/
  examples/
  toolchain/
  runtime/
  tests/
```

## Minimal prototype usage

From the repository root:

```bash
python -m toolchain.parser.cli examples/users/users.astra
```

The current parser prototype recognizes a small subset of the language:

- `module`
- `schema`
- `command`
- `event`
- `query`
- `enum`
- fields in block declarations

## Near-term roadmap

1. Expand grammar coverage
2. Add binder and symbol table
3. Add type checker
4. Add effect analysis
5. Build artifact graph
6. Add JSON/OpenAPI emitters

## Positioning

Astra is not centered on OOP/SOLID.
It is centered on artifacts, contracts, schemas, workflows, policies, effects, and AI-safe evolution.
