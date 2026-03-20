from toolchain.compiler.artifact_graph import build_artifact_graph
from toolchain.compiler.loader import load_modules


def test_module_loader_and_artifact_graph_across_files(tmp_path):
    (tmp_path / "common.astra").write_text(
        """
module common

type UserId = Uuid

event UserRegistered {
  userId: UserId
}
""",
        encoding="utf-8",
    )
    (tmp_path / "users.astra").write_text(
        """
module users

import common

command RegisterUser {
}

handle RegisterUser -> UserRegistered with effects [emit] {
}
""",
        encoding="utf-8",
    )

    module_graph = load_modules(tmp_path)
    assert set(module_graph.modules.keys()) == {"common", "users"}
    artifact_graph = build_artifact_graph(module_graph)
    assert not artifact_graph.diagnostics.has_errors()
    edge_kinds = {edge.kind for edge in artifact_graph.edges}
    assert "imports" in edge_kinds
    assert "handles" in edge_kinds
    assert "emits" in edge_kinds


def test_module_loader_reports_missing_import(tmp_path):
    (tmp_path / "users.astra").write_text(
        """
module users

import missing

command RegisterUser {
}
""",
        encoding="utf-8",
    )
    module_graph = load_modules(tmp_path)
    codes = {item.code for item in module_graph.diagnostics.items}
    assert "ASTRA4004" in codes
