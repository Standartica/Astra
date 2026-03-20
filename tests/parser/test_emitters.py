from toolchain.compiler.loader import load_modules
from toolchain.emitters.jsonschema import emit_json_schema
from toolchain.emitters.openapi import emit_openapi


def test_emitters_generate_json_schema_and_openapi_for_workspace(tmp_path):
    (tmp_path / "common.astra").write_text(
        """
module common
export UserId

type UserId = Uuid
""",
        encoding="utf-8",
    )
    (tmp_path / "users.astra").write_text(
        """
module users
import common
export User
export RegisterUser
export GetUserProfile
export Users

schema User {
  id: common.UserId
  email: Email
}

command RegisterUser {
  email: Email
}

query GetUserProfile {
  input: common.UserId
  output: User
}

api Users {
  post "/users" -> RegisterUser
  get "/users/{userId}" -> GetUserProfile
}
""",
        encoding="utf-8",
    )
    graph = load_modules(tmp_path)
    json_schema = emit_json_schema(graph)
    openapi = emit_openapi(graph)

    assert "users.User" in json_schema["$defs"]
    assert "/users" in openapi["paths"]
    assert "/users/{userId}" in openapi["paths"]
    assert "users.User" in openapi["components"]["schemas"]
