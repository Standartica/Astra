from toolchain.compiler.compatibility import compare_module_graphs
from toolchain.compiler.loader import load_modules


def test_compatibility_reports_breaking_changes(tmp_path):
    previous = tmp_path / "v1"
    current = tmp_path / "v2"
    previous.mkdir()
    current.mkdir()
    (previous / "users.astra").write_text(
        """
module users
export User
export Users
export GetUser

schema User {
  id: UserId
  email: Email
  name: String
}

api Users {
  get "/users/{id}" -> GetUser
}

query GetUser {
  input: UserId
  output: User
}
""",
        encoding="utf-8",
    )
    (current / "users.astra").write_text(
        """
module users
export User
export Users

schema User {
  id: UserId
  email: Email
}

api Users {
}
""",
        encoding="utf-8",
    )
    result = compare_module_graphs(load_modules(previous), load_modules(current))
    codes = {item.code for item in result.diagnostics.items}
    assert "ASTRA6003" in codes
    assert "ASTRA6001" in codes or "ASTRA6008" in codes


def test_compatibility_reports_non_breaking_additions(tmp_path):
    previous = tmp_path / "v1"
    current = tmp_path / "v2"
    previous.mkdir()
    current.mkdir()
    (previous / "users.astra").write_text(
        """
module users
export RegisterUser

command RegisterUser {
  email: Email
}
""",
        encoding="utf-8",
    )
    (current / "users.astra").write_text(
        """
module users
export RegisterUser

command RegisterUser {
  email: Email
  source: String
}
""",
        encoding="utf-8",
    )
    result = compare_module_graphs(load_modules(previous), load_modules(current))
    codes = {item.code for item in result.diagnostics.items}
    assert "ASTRA6101" in codes
