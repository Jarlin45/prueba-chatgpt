"""GitHub repository inspection engine.

Collects evidence directly from GitHub's public API. The engine does not decide
whether something is a problem; it gathers only the evidence selected by the
active skill.
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

    def inspect_repository(self, repository: str, paths: List[str] = None, recursive: bool = False) -> Dict[str, Any]:
        """Inspect repository structure and selected existing paths.

        When recursive is enabled, selected directories are traversed so that
        structural analysis can inspect the actual files inside them.
        """
        base = "https://api.github.com/repos/" + repository
        root = self._get(base + "/contents/")
        root_paths = {item.get("path") for item in root}
        selected = paths or ["SYSTEM", "api", "vercel.json", "index.html", "README.md"]

        evidence = {
            "repository": repository,
            "root_entries": [
                {"name": item.get("name"), "path": item.get("path"), "type": item.get("type")}
                for item in root
            ],
            "inspected_paths": [],
            "skipped_paths": [],
        }

        visited = set()

        def inspect_path(path: str, allow_recursive: bool = False) -> None:
            if path in visited:
                return
            visited.add(path)

            try:
                data = self._get(base + "/contents/" + path)
            except Exception as exc:
                evidence["skipped_paths"].append({"path": path, "reason": str(exc)})
                return

            if isinstance(data, list):
                evidence["inspected_paths"].append({
                    "path": path,
                    "type": "directory",
                    "entries": [
                        {"name": item.get("name"), "path": item.get("path"), "type": item.get("type")}
                        for item in data
                    ],
                })
                if allow_recursive:
                    for item in data:
                        child = item.get("path")
                        if child:
                            inspect_path(child, allow_recursive=True)
                return

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

        for path in selected:
            if path.split("/")[0] not in root_paths and path not in root_paths:
                evidence["skipped_paths"].append({"path": path, "reason": "not_present_at_repository_root"})
                continue
            inspect_path(path, allow_recursive=recursive)

        return evidence
