# Astra Semantics v0.1 Draft

## `module`
Groups related artifacts into one semantic unit.

## `schema`
Declares a nominal structured type and serves as a source for validation, transport, storage hints, and generation.

## `command`
Declares an intent to change the system.

## `event`
Declares an immutable fact that has happened.

## `query`
Declares a typed read operation.


## Recent draft additions

- `import` declarations and module-level dependency graph
- `type` aliases for domain-specific value types
- `query authorize PolicyName` binding
- `invariant` declarations
- `api` blocks with HTTP routes targeting `command` or `query`
- source-aware diagnostics with line/column/snippet output
