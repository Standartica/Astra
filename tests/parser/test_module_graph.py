from toolchain.compiler.artifact_graph import build_artifact_graph
from toolchain.compiler.loader import load_modules


def test_module_graph_and_artifact_graph(tmp_path):
    (tmp_path / "common.astra").write_text("module common\nexport UserId\ntype UserId = Uuid\n", encoding="utf-8")
    (tmp_path / "users.astra").write_text(
        """
module users
import common as core
command RegisterUser {
  id: core.UserId
}
api Users {
  post "/users" -> RegisterUser
}
""",
        encoding="utf-8",
    )
    graph = load_modules(tmp_path)
    artifact = build_artifact_graph(graph)
    assert len(graph.modules) == 2
    assert any(edge.kind.startswith("imports:") for edge in artifact.edges)
