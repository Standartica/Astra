# RFC 0003: Core Semantics

## Status
Draft

## Summary

Define the initial semantic model of Astra.

## Semantic categories

### Schema semantics
Schemas define nominal typed structures and metadata for contracts and state.

### Command semantics
Commands represent intent.

### Event semantics
Events represent immutable facts.

### Query semantics
Queries represent typed reads.

### Transition semantics
Handlers and workflows define valid transitions and orchestration.

### Policy semantics
Policies define typed authorization and guard logic.

### Invariant semantics
Invariants define state rules that valid transitions must preserve.

## Key semantic rule

Astra programs should make state transitions and effects explicit, not hidden inside opaque object behavior.
