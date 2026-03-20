# Astra Effects v0.1 Draft

## Motivation

Astra treats side effects as first-class and explicit.

This is necessary for:

- safer refactoring
- deterministic workflows
- better compiler diagnostics
- AI-readable execution boundaries

## Effect categories

Initial effect categories:

- `db.read`
- `db.write`
- `emit`
- `http.call`
- `mail.send`
- `fs.read`
- `fs.write`
- `clock`
- `ids`
- `schedule`
- `await.signal`
- `ui.prompt`

## Pure functions

```astra
fn normalizeEmail(value: String) -> Email
  pure
{
  value.trim().lower()
}
```

A pure function must not perform effects.

## Effectful functions

```astra
fn loadUser(id: UserId) -> Option<User>
  effects [db.read]
{
  db.users.find(id)
}
```

## Handler effects

Handlers must declare their effects explicitly.

```astra
handle RegisterUser -> UserRegistered
  effects [db.write, emit, clock, ids]
{
  // ...
}
```

## Workflow restrictions

Deterministic workflows may only use a restricted subset of operations.

They must not directly perform uncontrolled nondeterministic behavior.

Examples of forbidden direct behavior in deterministic workflows:

- reading wall-clock time directly
- generating random values directly
- arbitrary IO

Instead, workflow-safe boundaries and runtime abstractions must be used.
