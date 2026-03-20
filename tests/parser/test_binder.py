from toolchain.compiler.binder import bind_module
from toolchain.parser.parser import parse_source


def test_binder_reports_unknown_types_and_missing_symbols():
    source = """
module broken

command RegisterUser {
  email: MissingType
}

query GetUserProfile {
  input: UserId
  output: User
  authorize MissingPolicy
}

handle RegisterUser -> MissingEvent with effects [emit] {
}

api Users {
  post "/users" -> UnknownTarget
}
"""
    module = parse_source(source)
    result = bind_module(module, source=source)
    codes = {item.code for item in result.diagnostics.items}
    assert "ASTRA2001" in codes
    assert "ASTRA2004" in codes
    assert "ASTRA2006" in codes
    assert "ASTRA3002" in codes


def test_binder_accepts_builtin_domain_types_and_api_routes():
    source = """
module users

schema User {
  id: UserId
  email: Email
}

command RegisterUser {
  email: Email
}

query GetUserProfile {
  input: UserId
  output: User
}

event UserRegistered {
  userId: UserId
}

handle RegisterUser -> UserRegistered with effects [emit] {
}

api Users {
  post "/users" -> RegisterUser
  get "/users/{userId}" -> GetUserProfile
}
"""
    module = parse_source(source)
    result = bind_module(module, source=source)
    assert not result.diagnostics.has_errors()
