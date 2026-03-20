# Astra

Astra is a draft programming language and toolchain for AI-Native Artifact-Driven Architecture.

## Current repository state

This repository currently contains:

- language vision and design drafts
- RFC-style specification files
- a sample `.astra` module
- a Python prototype for tokenizer, parser, binder, and diagnostics

## Repository layout

```text
Astra/
  docs/
  specs/
  examples/
  toolchain/
  runtime/
  tests/
```

## Prototype commands

Parse an Astra file:

```bash
python -m toolchain.parser.cli examples/users/users.astra
```

Parse + bind + emit diagnostics:

```bash
python -m toolchain.compiler.cli examples/users/users.astra
```

Run tests:

```bash
python -m pytest
```

## Supported prototype grammar

Current prototype can parse these artifact kinds:

- `module`
- `schema`
- `enum`
- `capability`
- `command`
- `event`
- `query`
- `policy`
- `workflow`
- `handle`
- `fn`

This is still an early draft and not a stable language implementation.
