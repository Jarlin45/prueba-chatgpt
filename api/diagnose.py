import json
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen


def github_evidence(repo):
    url = "https://api.github.com/repos/" + repo
    req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "personal-system-diagnose"})
    with urlopen(req, timeout=10) as response:
        data = json.load(response)
    return {"repository_visible": True, "repository": data.get("full_name"), "default_branch": data.get("default_branch"), "private": data.get("private"), "source": "GitHub public API"}


def diagnose(problem, repo):
    evidence = github_evidence(repo)
    findings = []
    return {"status": "no_findings", "problem": problem, "findings": findings, "evidence": evidence, "verification": {"executed": True, "evidence_based": True}}


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
            self.end_headers()
            self.wfile.write(body)
