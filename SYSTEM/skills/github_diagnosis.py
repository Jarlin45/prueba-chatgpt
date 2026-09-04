"""Evidence-selection skill for repository diagnosis.

The skill classifies the user's problem and produces a small, explicit evidence
plan. It does not fetch files or decide the final diagnosis.
"""
import re


class GitHubDiagnosisSkill:
    name = "github-diagnosis"

    def diagnose(self, problem, engines):
        if "github" not in problem.description.lower():
            return []

        engine = engines.get("github")
        if engine is None:
            return []

        check = getattr(engine, "check_access", None)
        if check is None:
            return []

        result = check(problem.context)
        if result.get("ok"):
            return []

        return [{
            "source": self.name,
            "severity": result.get("severity", "medium"),
            "message": result.get("message", "GitHub access requires attention."),
        }]

    def plan_evidence(self, problem):
        """Return the minimum useful repository evidence for this problem."""
        text = (problem or "").lower()

        # Explicit file-existence/content requests take priority over generic
        # structural keywords such as "archivo". The engine receives a special
        # filename-search marker so it can search the repository recursively.
        filename = self._extract_requested_filename(problem or "")
        if filename and any(term in text for term in (
            "existe", "existencia", "buscar", "busca", "comprobar", "comprueba",
            "comprobar si", "analizar su contenido", "analiza su contenido",
            "contenido",
        )):
            problem_type = "repository_file"
            candidates = ["__FILE_SEARCH__:" + filename]
        # Structural/duplication problems take priority over frontend/API
        # keywords because the same problem can mention both concepts.
        elif any(word in text for word in (
            "estructura", "ruta", "path", "duplicado", "duplicate",
            "conflicto", "conflicts", "archivo", "carpeta", "directory",
            "misma función", "mismo archivo", "copia", "duplicada",
        )):
            problem_type = "repository_structure"
            candidates = [
                "SYSTEM", "api", "vercel.json", "index.html", "README.md",
            ]
        elif any(word in text for word in (
            "vercel", "deploy", "deployment", "despliegue", "build", "runtime",
            "producción", "production", "compila", "compilación",
        )):
            problem_type = "deployment"
            candidates = [
                "vercel.json", "api", ".python-version", "package.json",
                "pyproject.toml", "requirements.txt",
            ]
        elif any(word in text for word in (
            "botón", "button", "interfaz", "frontend", "fetch", "endpoint",
            "api", "respuesta", "no responde", "request", "post",
        )):
            problem_type = "frontend_api"
            candidates = [
                "index.html", "api/diagnose.py", "SYSTEM/web/index.html",
                "SYSTEM/api/diagnose.py",
            ]
        elif any(word in text for word in (
            "github", "repositorio", "repo", "permiso", "permission",
            "autenticación", "authentication", "acceso", "access",
        )):
            problem_type = "github_access"
            candidates = ["README.md", "SYSTEM", "api"]
        else:
            problem_type = "general"
            candidates = ["SYSTEM", "api", "vercel.json", "index.html", "README.md"]

        return {
            "skill": self.name,
            "problem_type": problem_type,
            "evidence_plan": candidates,
        }

    @staticmethod
    def _extract_requested_filename(problem):
        """Extract a concrete filename from an explicit repository-file request."""
        patterns = (
            r"`([^`]+\.[A-Za-z0-9_-]+)`",
            r"\b([A-Za-z0-9_.-]+\.(?:py|js|ts|tsx|jsx|json|html|css|md|txt|yml|yaml|toml|sql|env))\b",
        )
        for pattern in patterns:
            match = re.search(pattern, problem)
            if match:
                return match.group(1).strip()
        return None
