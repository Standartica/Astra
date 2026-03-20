# RFC 0002: Core Syntax

## Status
Draft

## Summary

Define the first stable draft of Astra surface syntax.

## Proposed core declarations

- `module`
- `schema`
- `enum`
- `union`
- `command`
- `event`
- `query`
- `projection`
- `workflow`
- `policy`
- `capability`
- `api`
- `view`
- `invariant`
- `fn`
- `handle`
- `resolve`
- `project`
- `design`
- `derive`
- `guardrails`

## Design principles

- readable by humans
- predictable for AI
- low hidden magic
- explicit declaration boundaries
- minimal ceremony

## Deferred topics

- imports
- namespaces beyond `module`
- macros/metaprogramming
- generic constraints
- pattern matching details
