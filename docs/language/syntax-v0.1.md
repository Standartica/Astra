# Astra Syntax v0.1 Draft

## File structure

A source file typically starts with a module declaration:

```astra
module users
```

A module may contain a mixture of declarative and executable artifacts.

## Core declarations

### Schema

```astra
schema User {
  id: UserId
  email: Email @unique
  name: NonEmptyString
  status: UserStatus = Pending
}
```

### Enum

```astra
enum UserStatus {
  Pending
  Active
  Suspended
}
```

### Command

```astra
command RegisterUser {
  email: Email
  name: NonEmptyString
}
```

### Event

```astra
event UserRegistered {
  userId: UserId
  at: Instant
}
```

### Query

```astra
query GetUserProfile {
  input userId: UserId
  output User
}
```

### Policy

```astra
policy CanReadUser(actor: Principal, userId: UserId) {
  require actor has ReadUsers
}
```

### Capability

```astra
capability ReadUsers
capability ManageUsers
```

### API

```astra
api Users {
  post "/users" => RegisterUser
  get "/users/{userId}" => GetUserProfile
}
```

### View

```astra
view UsersPage {
  source users: User[]
  action create => RegisterUser
}
```

## Executable forms

### Pure function

```astra
fn normalizeEmail(value: String) -> Email
  pure
{
  value.trim().lower()
}
```

### Handler

```astra
handle RegisterUser -> UserRegistered
  effects [db.write, emit, clock, ids]
{
  let id = ids.new()
  let now = clock.now()
  // ...
}
```

### Query resolver

```astra
resolve GetUserProfile
  effects [db.read]
{
  db.users.require(input.userId)
}
```

### Projection materializer

```astra
project UserListItem from User
  pure
{
  UserListItem {
    id = source.id,
    name = source.name,
    email = source.email
  }
}
```

## AI-native declarations

### Design note

```astra
design UserRegistration {
  goal: "Create account with email verification"
  assumptions:
    - "Email must be unique"
}
```

### Derive block

```astra
derive from RegisterUser:
  form
  openapi
  ts-client
```

### Guardrails

```astra
guardrails UsersModule {
  preserve api Users
  forbid breaking change on schema User.id
}
```
