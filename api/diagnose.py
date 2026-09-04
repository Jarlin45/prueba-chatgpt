import json
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from SYSTEM.engines.github_engine import GitHubEngine
from SYSTEM.skills.github_diagnosis import GitHubDiagnosisSkill
from SYSTEM.core.evidence_analyzer import EvidenceAnalyzer


def github_evidence(repo):
    url = "https://api.github.com/repos/" + repo
    req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "personal-system-diagnose"})
    with urlopen(req, timeout=10) as response:
        data = json.load(response)
    return {"repository_visible": True, "repository": data.get("full_name"), "default_branch": data.get("default_branch"), "private": data.get("private"), "source": "GitHub public API"}


def diagnose(problem, repo):
    access = github_evidence(repo)
    skill = GitHubDiagnosisSkill()
    plan = skill.plan_evidence(problem)
    recursive = plan["problem_type"] in ("repository_structure", "repository_file")
    inspection = GitHubEngine().inspect_repository(repo, plan["evidence_plan"], recursive=recursive)
    analysis = EvidenceAnalyzer().analyze(problem, plan["problem_type"], inspection)
    return {
        "status": "analysis_ready",
        "problem": problem,
        "problem_type": plan["problem_type"],
        "evidence_plan": plan["evidence_plan"],
        "findings": analysis["findings"],
        "analysis": analysis,
        "evidence": access,
        "inspection": inspection,
        "verification": {
            "executed": True,
            "evidence_based": True,
            "repository_inspected": True,
            "evidence_plan_applied": True,
            "evidence_analyzed": True,
        },
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            problem = payload.get("problem", "").strip()
            repo = payload.get("repository", "").strip()
            if not problem or not repo or "/" not in repo:
                raise ValueError("Se requiere problem y repository en formato owner/repo")
            body = json.dumps(diagnose(problem, repo), ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False).encode()
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
