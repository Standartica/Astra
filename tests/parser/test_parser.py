from toolchain.parser.parser import parse_source


def test_parse_schema_and_api():
    module = parse_source(
        """
module users
schema User {
  id: UserId
}
api Users {
  get "/users/{id}" -> GetUser
}
"""
    )
    assert module.name == "users"
    assert module.schemas[0].name == "User"
    assert module.apis[0].routes[0].path == "/users/{id}"
