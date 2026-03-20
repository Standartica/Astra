# Astra compiler skeleton

Current prototype stages:

- parse `.astra` source into AST
- build a symbol table and lightweight semantic model
- validate basic type references and artifact links
- validate `api` routes and `query authorize` bindings
- produce source-aware diagnostics with line/column/snippet data

Planned next steps:

- module graph loader across files
- richer type checking
- effect propagation analysis
- artifact graph emission
- first emitter prototypes
