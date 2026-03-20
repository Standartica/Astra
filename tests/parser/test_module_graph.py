from toolchain.compiler.artifact_graph import build_artifact_graph
from toolchain.compiler.loader import load_modules


def test_module_loader_and_artifact_graph_across_files(tmp_path):
    (tmp_path / "common.astra").write_text(
        """
module common

export UserId
export UserRegistered

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

import common as c

command RegisterUser {
}

handle RegisterUser -> c.UserRegistered with effects [emit] {
}
""",
        encoding="utf-8",
    )

    module_graph = load_modules(tmp_path)
    assert set(module_graph.modules.keys()) == {"common", "users"}
    artifact_graph = build_artifact_graph(module_graph)
    assert not artifact_graph.diagnostics.has_errors()
    edge_kinds = {edge.kind for edge in artifact_graph.edges}
    assert any(kind.startswith("imports:") for kind in edge_kinds)
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


def test_binder_reports_ambiguous_imported_reference(tmp_path):
    (tmp_path / "a.astra").write_text(
        """
module a
export SharedEvent

event SharedEvent {}
""",
        encoding="utf-8",
    )
    (tmp_path / "b.astra").write_text(
        """
module b
export SharedEvent

event SharedEvent {}
""",
        encoding="utf-8",
    )
    (tmp_path / "users.astra").write_text(
        """
module users
import a
import b

command RegisterUser {}
handle RegisterUser -> SharedEvent with effects [emit] {}
""",
        encoding="utf-8",
    )
    artifact_graph = build_artifact_graph(load_modules(tmp_path))
    codes = {item.code for item in artifact_graph.diagnostics.items}
    assert "ASTRA5001" in codes


def test_binder_reports_unknown_qualified_alias(tmp_path):
    (tmp_path / "common.astra").write_text(
        """
module common
export UserRegistered

event UserRegistered {}
""",
        encoding="utf-8",
    )
    (tmp_path / "users.astra").write_text(
        """
module users
import common as c

command RegisterUser {}
handle RegisterUser -> x.UserRegistered with effects [emit] {}
""",
        encoding="utf-8",
    )
    artifact_graph = build_artifact_graph(load_modules(tmp_path))
    codes = {item.code for item in artifact_graph.diagnostics.items}
    assert "ASTRA5002" in codes
