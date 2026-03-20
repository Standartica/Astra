# Architecture Overview

Astra has two major parts:

1. **Language layer**
2. **Toolchain/runtime layer**

## Language layer

The language layer defines first-class artifacts such as:

- `schema`
- `command`
- `event`
- `query`
- `workflow`
- `policy`
- `capability`
- `projection`
- `view`
- `api`
- `invariant`

It also defines executable artifacts:

- `fn`
- `handle`
- `resolve`
- `project`

## Toolchain layer

The toolchain is expected to provide:

- parser
- binder
- type checker
- effect analyzer
- artifact graph builder
- compatibility analyzer
- emitters

## Runtime layer

The runtime is expected to provide:

- execution of handlers
- query resolution
- workflow runtime
- adapter model
- state persistence abstractions
- effect boundaries

## Artifact graph

The compiler should build a graph that relates:

- source schemas to views and APIs
- commands to handlers and workflows
- queries to views and APIs
- policies to protected resources
- invariants to state transitions
- derivations to generated outputs

This artifact graph is central to Astra's AI-native design.
