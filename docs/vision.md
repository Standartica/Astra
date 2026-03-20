# Vision

## Problem

Traditional software architecture often centers around:

- classes
- services
- repositories
- dependency injection
- hidden runtime behavior
- implicit conventions

That model works, but it is not optimal for AI-assisted software development.

AI systems perform better when the system is expressed through:

- explicit contracts
- formal schemas
- typed commands and events
- observable state transitions
- declared effects
- constrained workflows

## Astra thesis

Astra is based on the following thesis:

> A software system should be described through formal artifacts of intent, state, policy, and effect, and executable code should be a controlled derivative of that model.

## High-level goals

Astra aims to provide:

- an artifact-first language
- a compiler that builds an artifact graph, not only an AST
- AI-readable and machine-checkable architecture
- a language-native workflow model
- an explicit effect model
- derivation of server, client, UI, and docs artifacts from shared source definitions

## Why this matters

This approach helps with:

- safer AI-generated code
- traceable system evolution
- better compatibility checks
- more deterministic refactoring
- multi-target generation
- reduced architectural drift

## Intended domains

Astra is particularly suited for:

- business systems
- internal tools
- SaaS applications
- operational platforms
- workflow-heavy systems
- offline-capable applications
- policy-sensitive systems
