from toolchain.parser.parser import parse_source


SOURCE = """
module users

schema User {
  id: UserId
  email: Email
}

enum UserStatus {
  Pending
  Active
}

capability ReadUsers

command RegisterUser {
  email: Email
}

event UserRegistered {
  userId: UserId
}

query GetUserProfile {
  input: UserId
  output: User
}

policy CanReadUser(actor: Principal, userId: UserId) {
  require actor has ReadUsers
}

workflow OnboardUser(userId: UserId) deterministic {
  step createWorkspace
  step awaitEmailConfirmation timeout seven-days
}

handle RegisterUser -> UserRegistered with effects [db.write, emit] {
}

fn normalizeEmail(value: String) -> Email pure {
}
"""


def test_parser_supports_core_artifacts():
    module = parse_source(SOURCE)
    assert module.name == "users"
    assert len(module.schemas) == 1
    assert len(module.enums) == 1
    assert len(module.capabilities) == 1
    assert len(module.commands) == 1
    assert len(module.events) == 1
    assert len(module.queries) == 1
    assert len(module.policies) == 1
    assert len(module.workflows) == 1
    assert len(module.handles) == 1
    assert len(module.functions) == 1
    assert module.functions[0].purity == "pure"
