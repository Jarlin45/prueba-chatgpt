"""GitHub repository inspection engine.

Collects evidence directly from GitHub's public API. The engine does not decide
whether something is a problem; it gathers the repository evidence that the
orchestrator/skill can reason about.
"""
from typing import Any, Dict, List
from urllib.request import Request, urlopen
import json


class GitHubEngine:
    name = "github"

    def _get(self, url: str) -> Any:
        req = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "personal-system-diagnose",
            },
        )
        with urlopen(req, timeout=10) as response:
            return json.load(response)

    def check_access(self, context: Dict[str, Any]) -> Dict[str, Any]:
        required = ("authenticated", "app_installed", "repository_visible")
        missing = [key for key in required if context.get(key) is not True]
        if missing:
            return {
                "ok": False,
                "severity": "high" if "authenticated" in missing else "medium",
                "message": "GitHub access is incomplete; missing checks: " + ", ".join(missing),
            }
        return {
            "ok": True,
            "message": "GitHub authentication, app installation and repository visibility checks passed.",
            "writable": context.get("writable") is True,
        }

    def inspect_repository(self, repository: str, paths: List[str] = None) -> Dict[str, Any]:
        """Inspect repository structure and selected files without cloning it."""
        base = "https://api.github.com/repos/" + repository
        root = self._get(base + "/contents/")
        selected = paths or ["SYSTEM", "api", "vercel.json", "index.html", "README.md"]

        evidence = {
            "repository": repository,
            "root_entries": [
                {"name": item.get("name"), "path": item.get("path"), "type": item.get("type")}
                for item in root
            ],
            "inspected_paths": [],
        }

        for path in selected:
            data = self._get(base + "/contents/" + path)
            if isinstance(data, list):
                evidence["inspected_paths"].append({
                    "path": path,
                    "type": "directory",
                    "entries": [
                        {"name": item.get("name"), "path": item.get("path"), "type": item.get("type")}
                        for item in data
                    ],
                })
            else:
                content = data.get("content", "")
                if data.get("encoding") == "base64":
                    import base64
                    try:
                        content = base64.b64decode(content).decode("utf-8")
                    except Exception:
                        content = ""
                evidence["inspected_paths"].append({
                    "path": path,
                    "type": "file",
                    "size": data.get("size"),
                    "sha": data.get("sha"),
                    "content": content,
                })

        return evidence
