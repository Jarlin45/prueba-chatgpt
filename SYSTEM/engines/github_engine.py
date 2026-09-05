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
        req = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "personal-system-diagnose"})
        with urlopen(req, timeout=10) as response:
            return json.load(response)

    def check_access(self, context: Dict[str, Any]) -> Dict[str, Any]:
        required = ("authenticated", "app_installed", "repository_visible")
        missing = [key for key in required if context.get(key) is not True]
        if missing:
            return {"ok": False, "severity": "high" if "authenticated" in missing else "medium", "message": "GitHub access is incomplete; missing checks: " + ", ".join(missing)}
        return {"ok": True, "message": "GitHub authentication, app installation and repository visibility checks passed.", "writable": context.get("writable") is True}

    def inspect_repository(self, repository: str, paths: List[str] = None, recursive: bool = False) -> Dict[str, Any]:
        """Inspect only the evidence selected by the active skill."""
        base = "https://api.github.com/repos/" + repository
        selected = paths or ["SYSTEM", "api", "vercel.json", "index.html", "README.md"]
        evidence = {
            "repository": repository,
            "root_entries": [],
            "inspected_paths": [],
            "skipped_paths": [],
            "requested_evidence": list(selected),
            "repository_state": {"empty": False, "root_inspectable": True},
        }

        # GitHub's contents endpoint returns an error for a repository with no
        # commit/tree. Preserve that state explicitly instead of manufacturing
        # file evidence or interpreting a failed lookup as a successful read.
        try:
            root = self._get(base + "/contents/")
        except Exception as exc:
            evidence["repository_state"] = {
                "empty": True,
                "root_inspectable": False,
                "reason": str(exc),
            }
            for path in selected:
                evidence["skipped_paths"].append({"path": path, "reason": "repository_empty_or_uninspectable"})
            return evidence

        root_paths = {item.get("path") for item in root}
        evidence["root_entries"] = [{"name": item.get("name"), "path": item.get("path"), "type": item.get("type")} for item in root]
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
                evidence["inspected_paths"].append({"path": path, "type": "directory", "entries": [{"name": item.get("name"), "path": item.get("path"), "type": item.get("type")} for item in data]})
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
            evidence["inspected_paths"].append({"path": path, "type": "file", "size": data.get("size"), "sha": data.get("sha"), "content": content})

        def search_filename(requested: str) -> None:
            # A repository-relative path is an exact target. Do not broaden it
            # to a basename search, which could inspect unrelated duplicates.
            if "/" in requested:
                if requested.split("/", 1)[0] in root_paths:
                    inspect_path(requested)
                else:
                    evidence["skipped_paths"].append({"path": requested, "reason": "file_not_found"})
                return

            matches = []
            def walk(path: str = "") -> None:
                try:
                    data = root if path == "" else self._get(base + "/contents/" + path)
                except Exception as exc:
                    if path:
                        evidence["skipped_paths"].append({"path": path, "reason": str(exc)})
                    return
                if not isinstance(data, list):
                    return
                for item in data:
                    child, name = item.get("path"), item.get("name")
                    if not child:
                        continue
                    if item.get("type") == "file" and name == requested:
                        inspect_path(child)
                        matches.append(child)
                    elif item.get("type") == "dir":
                        walk(child)
            walk()
            if not matches:
                evidence["skipped_paths"].append({"path": requested, "reason": "file_not_found"})

        for path in selected:
            if path.startswith("__FILE_SEARCH__:"):
                search_filename(path.split(":", 1)[1])
                continue
            if path.split("/")[0] not in root_paths and path not in root_paths:
                evidence["skipped_paths"].append({"path": path, "reason": "not_present_at_repository_root"})
                continue
            inspect_path(path, allow_recursive=recursive)
        return evidence
