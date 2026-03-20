# Astra compiler skeleton

Current prototype stages:

- parse `.astra` source into AST
- build a symbol table and lightweight semantic model
- validate basic type references and artifact links
- validate `api` routes and `query authorize` bindings
- validate multi-module imports/exports/aliases
- build artifact graph across modules
- emit `JSON Schema` and `OpenAPI`
- compare exported artifact compatibility between two versions

Planned next steps:

- richer type checking
- effect propagation analysis
- semantic linker improvements
- first runtime and code-generation emitters
