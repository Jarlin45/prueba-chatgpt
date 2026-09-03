"""HTTP-friendly entry point for the adaptive construction system."""
from core.orchestrator import Orchestrator, Problem
from engines.github_engine import GitHubEngine
from skills.github_diagnosis import GitHubDiagnosisSkill


def build_system() -> Orchestrator:
    system = Orchestrator()
    system.register_engine("github", GitHubEngine())
    system.register_skill("github-diagnosis", GitHubDiagnosisSkill())
    return system


def diagnose(problem_text: str, context: dict) -> dict:
    system = build_system()
    problem = Problem(
        title="User problem",
        description=problem_text,
        context=context,
    )
    findings = system.run(problem)
    return {
        "status": "attention_required" if findings else "no_findings",
        "findings": findings,
        "verification": {
            "diagnosis_executed": True,
            "findings_count": len(findings),
        },
    }
