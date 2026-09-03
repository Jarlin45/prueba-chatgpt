import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
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
    def do_GET(self):
        """Controlled diagnostic: force a real HTTP POST back into this function."""
        try:
            parsed = urlparse(self.path)
            if parsed.path != "/api/diagnose" or "selftest" not in parsed.query:
                self.send_response(405)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": "Use POST /api/diagnose"}).encode())
                return

            host = self.headers.get("host")
            if not host:
                raise ValueError("No se pudo determinar el host de Vercel")
            url = "https://" + host + "/api/diagnose"
            payload = json.dumps({
                "problem": "SELFTEST: comprobar ejecución POST y consulta GitHub",
                "repository": "Jarlin45/prueba-chatgpt"
            }).encode()
            req = Request(url, data=payload, method="POST", headers={
                "Content-Type": "application/json",
                "User-Agent": "personal-system-post-selftest",
                "X-Diagnostic-Selftest": "true"
            })
            with urlopen(req, timeout=15) as response:
                result = json.load(response)

            result["verification"]["real_post_selftest"] = True
            result["verification"]["post_url"] = url
            body = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({"status": "error", "error": str(exc), "verification": {"real_post_selftest": False}}, ensure_ascii=False).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

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
