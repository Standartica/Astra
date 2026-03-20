# Astra Syntax v0.1 Draft

## Top-level declarations

Supported in the current draft:

- `module`
- `schema`
- `enum`
- `command`
- `event`
- `query`

Example:

```astra
module users

schema User {
  id: UserId
  email: Email
}

command RegisterUser {
  email: Email
  name: NonEmptyString
}
```
