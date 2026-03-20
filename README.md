# Astra

Astra is a draft programming language and platform for **AI-Native Artifact-Driven Architecture**.

It is designed as an **artifact-first, schema-centric, effect-aware, workflow-native** language and toolchain where the primary building blocks are not classes, but typed system artifacts:

- schemas
- commands
- events
- queries
- workflows
- policies
- capabilities
- projections
- views
- APIs
- invariants

The goal of Astra is to make software systems understandable to **humans, compilers, and AI systems at the same time**.

## Positioning

Astra is intended for designing and building:

- RESTful APIs
- SPA
- PWA
- client-server systems
- desktop applications

Astra is not OOP-first, framework-first, DB-first, or transport-first.

Astra is:

- artifact-first
- schema-first
- workflow-native
- effect-aware
- AI-oriented

## Repository structure

```text
Astra/
  README.md
  docs/
    vision.md
    architecture.md
    language/
      syntax-v0.1.md
      semantics-v0.1.md
      type-system-v0.1.md
      effects-v0.1.md
      compiler-pipeline-v0.1.md
  specs/
    astra-rfc-0001-vision.md
    astra-rfc-0002-core-syntax.md
    astra-rfc-0003-semantics.md
    astra-rfc-0004-effects.md
    astra-rfc-0005-compiler.md
  examples/
    users/
      users.astra
  toolchain/
    parser/
    compiler/
    emitters/
  runtime/
    core/
  tests/
```

## Current status

This repository is an early draft and contains:

- the language vision
- the first syntax proposal
- initial semantic model
- type system draft
- effects draft
- compiler pipeline draft
- one end-to-end example module

## Immediate goals

1. Stabilize `v0.1` surface syntax.
2. Define formal semantics for core artifacts.
3. Lock the first compiler pipeline.
4. Build parser + AST prototype.
5. Add first emitters:
   - JSON Schema
   - OpenAPI
   - TypeScript client
   - docs emitter

## Core idea

Astra treats software as a graph of formal artifacts.

Instead of centering design around service classes and object hierarchies, Astra centers it around:

- typed schemas
- commands and events
- explicit effects
- deterministic workflows
- authorization policies
- UI projections
- derivable outputs

This makes systems easier to generate, validate, evolve, and refactor with AI assistance.
