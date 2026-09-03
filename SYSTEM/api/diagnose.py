import json
from http.server import BaseHTTPRequestHandler


def diagnose(problem, evidence):
    """Diagnóstico HTTP independiente del proveedor de GitHub.

    evidence debe contener los datos observados por un motor externo.
    No inventa autenticación ni permisos.
    """
    findings = []
    if not evidence.get("repository_visible", False):
        findings.append({"source": "github", "severity": "warning", "message": "El repositorio no está confirmado como visible."})
    if evidence.get("authenticated") is False:
        findings.append({"source": "github", "severity": "warning", "message": "La autenticación de GitHub no está confirmada."})
    if evidence.get("app_installed") is False:
        findings.append({"source": "github", "severity": "warning", "message": "La instalación de la App de GitHub no está confirmada."})
    if evidence.get("writable") is False:
        findings.append({"source": "github", "severity": "warning", "message": "El permiso de escritura no está confirmado."})

    return {
        "status": "attention_required" if findings else "no_findings",
        "problem": problem,
        "findings": findings,
        "evidence": evidence,
        "verification": {"executed": True, "note": "El endpoint procesó la evidencia recibida; no afirma acceso que no haya sido aportado."},
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            result = diagnose(payload.get("problem", ""), payload.get("evidence", {}))
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
