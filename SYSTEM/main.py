"""End-to-end entry point for System v0.1."""
from core.orchestrator import Orchestrator, Problem
from engines.github_engine import GitHubEngine
from skills.github_diagnosis import GitHubDiagnosisSkill


def build_system() -> Orchestrator:
    system = Orchestrator()
    system.register_engine("github", GitHubEngine())
    system.register_skill("github-diagnosis", GitHubDiagnosisSkill())
    return system


def diagnose_github(context):
    system = build_system()
    problem = Problem(
        title="GitHub access diagnosis",
        description="Diagnose a GitHub connection problem.",
        context=context,
    )
    return system.run(problem)


if __name__ == "__main__":
    findings = diagnose_github({
        "authenticated": True,
        "app_installed": True,
        "repository_visible": True,
        "writable": True,
    })
    print("System v0.1")
    print("PASS: GitHub access checks passed." if not findings else findings)
