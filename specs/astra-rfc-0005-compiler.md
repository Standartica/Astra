# RFC 0005: Compiler and Artifact Graph

## Status
Draft

## Summary

Define the first compiler architecture for Astra.

## Compiler responsibilities

- parse source
- bind symbols
- type-check
- analyze effects
- build artifact graph
- emit diagnostics
- drive artifact emitters

## Artifact graph requirement

The compiler must build explicit edges between important artifacts.

Examples:

- command -> handler
- handler -> event
- query -> resolver
- query -> view
- policy -> protected artifact
- schema -> generated schema output

## Rationale

Without an artifact graph, Astra would collapse back into a conventional language with some annotations.

The artifact graph is one of the defining features of the platform.
