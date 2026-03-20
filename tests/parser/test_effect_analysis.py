from toolchain.compiler.effect_analysis import analyze_effects
from toolchain.compiler.loader import load_modules
from toolchain.compiler.semantic_ir import build_semantic_ir


def test_effect_analysis_reports_unknown_and_duplicate_effects(tmp_path):
    (tmp_path / "users.astra").write_text(
        """
module users

fn doWork() effects [db.read, db.read, mystery.fx] {
}
""",
        encoding="utf-8",
    )

    result = analyze_effects(build_semantic_ir(load_modules(tmp_path)))
    codes = {item.code for item in result.diagnostics.items}
    assert "ASTRA7001" in codes
    assert "ASTRA7002" in codes


def test_deterministic_workflow_cannot_reference_non_workflow_safe_function(tmp_path):
    (tmp_path / "users.astra").write_text(
        """
module users

fn sendWelcome() effects [mail.send] {
}

workflow Onboard(userId: UserId) deterministic {
  step sendWelcome
}
""",
        encoding="utf-8",
    )

    result = analyze_effects(build_semantic_ir(load_modules(tmp_path)))
    codes = {item.code for item in result.diagnostics.items}
    assert "ASTRA7004" in codes
