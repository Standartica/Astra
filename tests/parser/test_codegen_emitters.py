from toolchain.compiler.loader import load_modules
from toolchain.emitters.server_stubs import emit_server_stubs
from toolchain.emitters.ts_client import emit_ts_client


def test_codegen_emitters_generate_ts_client_and_server_stubs_for_workspace(tmp_path):
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
    server_stubs = emit_server_stubs(graph)

    assert "export interface User" in ts_client
    assert "export interface RegisterUser" in ts_client
    assert "class AstraClient" in ts_client
    assert "async registerUser(body: RegisterUser)" in ts_client
    assert "async getUserProfile(userId: string) : Promise<User>" in ts_client
    assert "RouteStub" in server_stubs
    assert "users.Users.RegisterUser" in server_stubs
    assert "response_model='User'" in server_stubs
    assert "const url = `${this.baseUrl}/users`;" in ts_client
    assert "const url = `${this.baseUrl}/users/${userId}`;" in ts_client
