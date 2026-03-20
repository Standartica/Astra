# Astra Type System v0.1 Draft

## Goals

The Astra type system should be:

- strongly typed
- readable
- emitter-friendly
- suitable for contracts and schemas
- suitable for static analysis and AI tooling

## Primitive types

- `Int`
- `Float`
- `Decimal`
- `Bool`
- `String`
- `Bytes`
- `Instant`
- `Duration`
- `Uuid`

## Generic containers

- `List<T>`
- `Set<T>`
- `Map<K, V>`
- `Option<T>`
- `Result<T, E>`

## Value types

Astra supports constrained named types.

```astra
type Email = String where isEmail(self)
type UserId = Uuid
type NonEmptyString = String where length(self.trim()) > 0
```

## Enums

Enums are nominal closed sets.

```astra
enum UserStatus {
  Pending
  Active
  Suspended
}
```

## Tagged unions

```astra
union PaymentMethod {
  Card(last4: String)
  BankTransfer(iban: String)
  Cash
}
```

## Schemas as types

A `schema` is a nominal type with additional metadata useful for:

- validation
- serialization
- API generation
- persistence hints
- form generation

## Compatibility concerns

The type system should eventually support compatibility categories such as:

- additive
- compatible
- breaking

This is important for artifact evolution and AI-assisted change analysis.
