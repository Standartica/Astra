# Astra Architecture Draft

Astra consists of four conceptual layers:

1. Artifact description layer
2. Pure logic layer
3. Effect-aware execution layer
4. Runtime adapter layer

The compiler pipeline is expected to build:

- AST
- symbol graph
- type graph
- effect graph
- artifact graph

The first prototype in this repository focuses only on a tiny subset:

- lexical analysis
- parsing
- AST generation
- CLI output
