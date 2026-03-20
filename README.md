# Astra

Astra is a draft programming language and toolchain for AI-Native Artifact-Driven Architecture.

Current prototype includes:
- tokenizer and parser
- binder and diagnostics
- module loader and artifact graph
- compatibility checks
- JSON Schema and OpenAPI emitters
- semantic IR
- effect analysis
- CLI and tests

## Quick start

```bash
python -m toolchain.compiler.cli examples/users/users.astra
python -m toolchain.compiler.cli examples/workspace
python -m toolchain.compiler.cli compat examples/compatibility/v1 examples/compatibility/v2
pytest -q
```
