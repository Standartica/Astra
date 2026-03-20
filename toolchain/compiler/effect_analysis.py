from __future__ import annotations

from dataclasses import dataclass, field

from toolchain.compiler.diagnostics import DiagnosticBag
from toolchain.compiler.semantic_ir import SemanticIRResult

KNOWN_EFFECTS = {
    "db.read": {"category": "database", "workflow_safe": False},
    "db.write": {"category": "database", "workflow_safe": False},
    "emit": {"category": "events", "workflow_safe": True},
    "http.call": {"category": "network", "workflow_safe": False},
    "mail.send": {"category": "integration", "workflow_safe": False},
    "fs.read": {"category": "filesystem", "workflow_safe": False},
    "fs.write": {"category": "filesystem", "workflow_safe": False},
    "clock": {"category": "nondeterminism", "workflow_safe": False},
    "ids": {"category": "nondeterminism", "workflow_safe": False},
    "schedule": {"category": "workflow", "workflow_safe": True},
    "await.signal": {"category": "workflow", "workflow_safe": True},
    "ui.prompt": {"category": "ui", "workflow_safe": False},
}


@dataclass(slots=True)
class EffectSummary:
    qualified_name: str
    artifact_kind: str
    declared_effects: list[str] = field(default_factory=list)
    unknown_effects: list[str] = field(default_factory=list)
    duplicate_effects: list[str] = field(default_factory=list)
    workflow_safe: bool = True


@dataclass(slots=True)
class EffectAnalysisResult:
    summaries: list[EffectSummary] = field(default_factory=list)
    diagnostics: DiagnosticBag = field(default_factory=DiagnosticBag)


def analyze_effects(ir: SemanticIRResult) -> EffectAnalysisResult:
    result = EffectAnalysisResult()
    result.diagnostics.extend(ir.diagnostics.items)
    function_effects: dict[str, list[str]] = {}

    for module_name, module in ir.modules.items():
        for fn in module.functions:
            qn = f"{module_name}.{fn.name}"
            function_effects[qn] = list(fn.effects)
            duplicates = sorted({effect for effect in fn.effects if fn.effects.count(effect) > 1})
            unknown = sorted({effect for effect in fn.effects if effect not in KNOWN_EFFECTS})
            if fn.purity == "pure" and fn.effects:
                result.diagnostics.add("error", "ASTRA7003", f"Pure function '{qn}' cannot declare effects")
            for effect in unknown:
                result.diagnostics.add("error", "ASTRA7001", f"Unknown effect '{effect}' declared by function '{qn}'")
            for effect in duplicates:
                result.diagnostics.add("warning", "ASTRA7002", f"Duplicate effect '{effect}' declared by function '{qn}'")
            workflow_safe = all(KNOWN_EFFECTS.get(effect, {}).get("workflow_safe", False) for effect in fn.effects if effect in KNOWN_EFFECTS)
            result.summaries.append(EffectSummary(qualified_name=qn, artifact_kind="fn", declared_effects=list(fn.effects), unknown_effects=unknown, duplicate_effects=duplicates, workflow_safe=workflow_safe))

        for handle in module.handles:
            qn = f"{module_name}.handle[{handle.command}]"
            duplicates = sorted({effect for effect in handle.effects if handle.effects.count(effect) > 1})
            unknown = sorted({effect for effect in handle.effects if effect not in KNOWN_EFFECTS})
            for effect in unknown:
                result.diagnostics.add("error", "ASTRA7001", f"Unknown effect '{effect}' declared by handle '{qn}'")
            for effect in duplicates:
                result.diagnostics.add("warning", "ASTRA7002", f"Duplicate effect '{effect}' declared by handle '{qn}'")
            workflow_safe = all(KNOWN_EFFECTS.get(effect, {}).get("workflow_safe", False) for effect in handle.effects if effect in KNOWN_EFFECTS)
            result.summaries.append(EffectSummary(qualified_name=qn, artifact_kind="handle", declared_effects=list(handle.effects), unknown_effects=unknown, duplicate_effects=duplicates, workflow_safe=workflow_safe))

    for module_name, module in ir.modules.items():
        for workflow in module.workflows:
            qn = f"{module_name}.{workflow.name}"
            for step in workflow.steps:
                if workflow.deterministic and step.resolved_kind == "fn" and step.resolved_qualified_name:
                    effects = function_effects.get(step.resolved_qualified_name, [])
                    disallowed = [effect for effect in effects if not KNOWN_EFFECTS.get(effect, {}).get("workflow_safe", False)]
                    if disallowed:
                        result.diagnostics.add(
                            "error",
                            "ASTRA7004",
                            f"Deterministic workflow '{qn}' references effectful function '{step.resolved_qualified_name}' with non-workflow-safe effects: {', '.join(sorted(disallowed))}",
                        )
            result.summaries.append(EffectSummary(qualified_name=qn, artifact_kind="workflow", workflow_safe=workflow.deterministic))
    return result
