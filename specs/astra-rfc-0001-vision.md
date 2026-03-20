# RFC 0001: Vision

## Status
Draft

## Summary

Define Astra as an artifact-first programming language and toolchain for AI-native software architecture.

## Motivation

Traditional OOP-centered architecture often distributes meaning across:

- classes
- service layers
- frameworks
- runtime conventions

This makes AI-assisted development more fragile and harder to validate.

Astra instead centers the system on formal artifacts.

## Decision

Astra will be designed around:

- schemas
- commands
- events
- queries
- workflows
- policies
- capabilities
- projections
- views
- explicit effects

## Consequences

Positive:

- stronger architectural traceability
- improved code generation
- better AI-guided refactoring
- multi-target derivation

Trade-offs:

- higher upfront formalization
- more compiler/toolchain complexity
- more opinionated architecture model
