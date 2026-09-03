"""Minimal orchestrator for the Personal Adaptive Construction System v0.1."""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Problem:
    title: str
    description: str
    context: Dict[str, str]


@dataclass
class Finding:
    source: str
    severity: str
    message: str


class Orchestrator:
    """Routes a real problem through skills, engines, verification and memory."""

    def __init__(self) -> None:
        self.skills: Dict[str, object] = {}
        self.engines: Dict[str, object] = {}

    def register_skill(self, name: str, skill: object) -> None:
        self.skills[name] = skill

    def register_engine(self, name: str, engine: object) -> None:
        self.engines[name] = engine

    def diagnose(self, problem: Problem) -> List[Finding]:
        findings: List[Finding] = []
        for skill in self.skills.values():
            diagnose = getattr(skill, "diagnose", None)
            if diagnose:
                findings.extend(diagnose(problem, self.engines))
        return findings

    def run(self, problem: Problem) -> List[Finding]:
        return self.diagnose(problem)
