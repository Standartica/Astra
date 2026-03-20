from toolchain.compiler.loader import load_modules
from toolchain.emitters.server_fastapi import emit_server_fastapi
from toolchain.emitters.ts_client import emit_ts_client


def test_codegen_emitters_generate_typed_ts_client_and_fastapi_stubs(tmp_path):
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
import common as core
export User
export RegisterUser
export GetUserProfile
export Users

schema User {
  id: core.UserId
  email: Email
}

command RegisterUser {
  email: Email
}

query GetUserProfile {
  input: core.UserId
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
    ts_client = emit_ts_client(graph)
    fastapi = emit_server_fastapi(graph)

    assert "export interface users_User" in ts_client
    assert "export async function users_Users_get_GetUserProfile" in ts_client
    assert "const url = `${client.baseUrl}/users/${encodeURIComponent(String(userId))}`;" in ts_client
    assert "class users_User(BaseModel):" in fastapi
    assert '@users_router.get("/users/{userId}", response_model=users_User)' in fastapi
    assert "async def users_Users_post_RegisterUser(payload: users_RegisterUser):" in fastapi
