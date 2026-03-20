from toolchain.compiler.loader import load_modules
from toolchain.compiler.semantic_ir import build_semantic_ir


def test_semantic_ir_resolves_qualified_types_and_api_targets(tmp_path):
    (tmp_path / "core.astra").write_text(
        """
module core
export UserId
export Email

type UserId = Uuid
type Email = String
""",
        encoding="utf-8",
    )
    (tmp_path / "users.astra").write_text(
        """
module users
import core as c

schema User {
  id: c.UserId
  email: c.Email
}

command RegisterUser {
  email: c.Email
}

query GetUserProfile {
  input: c.UserId
  output: User
}

api Users {
  post "/users" -> RegisterUser
  get "/users/{id}" -> GetUserProfile
}
""",
        encoding="utf-8",
    )

    ir = build_semantic_ir(load_modules(tmp_path))
    users = ir.modules["users"]
    assert users.schemas[0].fields[0].type_ref.qualified_name == "core.UserId"
    assert users.commands[0].fields[0].type_ref.qualified_name == "core.Email"
    assert users.apis[0].routes[0].target == "users.RegisterUser"
    assert users.apis[0].routes[1].target_kind == "query"
