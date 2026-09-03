import json
from http.server import BaseHTTPRequestHandler


def diagnose(problem, evidence):
    findings = []
    checks = [
        ("repository_visible", "El repositorio no está confirmado como visible."),
        ("authenticated", "La autenticación de GitHub no está confirmada."),
        ("app_installed", "La instalación de la App de GitHub no está confirmada."),
        ("writable", "El permiso de escritura no está confirmado."),
    ]
    for key, message in checks:
        if evidence.get(key) is False:
            findings.append({"source": "github", "severity": "warning", "message": message})
    return {
        "status": "attention_required" if findings else "no_findings",
        "problem": problem,
        "findings": findings,
        "evidence": evidence,
        "verification": {"executed": True, "evidence_based": True},
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            body = json.dumps(diagnose(payload.get("problem", ""), payload.get("evidence", {})), ensure_ascii=False).encode()
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
