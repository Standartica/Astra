# RFC 0002 — Core Syntax

This RFC defines the first parseable subset of Astra.

Included declarations:

- module
- schema
- enum
- command
- event
- query

Each block declaration uses the form:

```astra
schema Name {
  field: Type
}
```
