# Astra Semantics v0.1 Draft

## Semantic model

Astra defines a system through formal artifacts and explicit transitions.

The core semantic layers are:

1. **Schema semantics** — typed state and contracts
2. **Intent semantics** — commands as proposed changes
3. **Fact semantics** — events as immutable facts
4. **Transition semantics** — handlers and workflows as controlled transitions
5. **Effect semantics** — explicit side-effect boundaries

## Commands

A `command` is a typed intent to change system state.

A command is inert by itself. It only changes the system when interpreted by a `handle` block or a workflow step.

## Events

An `event` is a typed immutable fact representing something that has already happened.

Events are suitable for:

- audit trails
- workflows
- projections
- integration boundaries

## Queries

A `query` is a typed read contract. It does not mutate state.

## Handlers

A `handle` declaration interprets a command and may:

- validate input
- persist state
- emit events
- invoke declared effects

Handlers must stay within their declared effect set.

## Workflows

A `workflow` is a deterministic long-running process.

It coordinates commands, events, waits, timeouts, and retries.

A workflow is not just a helper function. It has separate runtime requirements:

- replayability
- resumability
- deterministic execution rules

## Policies

A `policy` is a typed authorization or guard rule. It is part of the semantic model and should be visible in the artifact graph.

## Views

A `view` is a projection-oriented UI contract, not just an implementation detail.

## Invariants

An `invariant` expresses a logical rule that must remain true across valid transitions.

Invariants should participate in:

- static analysis
- runtime checks
- generated tests
- AI guardrails
