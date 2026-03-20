# Astra Compiler Pipeline v0.1 Draft

## Overview

The Astra compiler should do more than parse syntax and type-check code.

It should build a complete semantic representation of the system, including an artifact graph.

## Pipeline stages

### 1. Parsing

- lex source text
- parse source files
- build AST

### 2. Binding

- resolve names
- build symbol tables
- connect module-level declarations

### 3. Typing

- validate types
- type-check schemas
- type-check handlers and resolvers
- check query and API contracts

### 4. Effect analysis

- validate declared effects
- propagate called effects
- enforce purity
- validate deterministic workflow rules

### 5. Artifact graph construction

Build explicit relationships among artifacts such as:

- schema -> query
- query -> view
- command -> handler
- handler -> event
- workflow -> command/event
- policy -> API/query/view

### 6. Diagnostics

Report:

- syntax errors
- type errors
- invalid effects
- policy attachment issues
- compatibility warnings
- invariant violations

### 7. Emitters

Use the artifact graph as input for:

- JSON Schema emitter
- OpenAPI emitter
- TypeScript client emitter
- docs emitter
- server stubs
- UI scaffolds
