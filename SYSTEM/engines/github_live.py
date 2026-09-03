"""Live GitHub evidence adapter.

This adapter is intentionally small: it converts GitHub connector evidence into
plain data that the diagnosis skill can consume. Authentication and installation
are established by successful connector calls; repository visibility and write
permission are checked against the target repository.
"""
from typing import Any, Dict


class GitHubLiveEngine:
    name = "github-live"

    def build_evidence(self, login_result: Dict[str, Any], accounts_result: Dict[str, Any], repo_result: Dict[str, Any], target: str) -> Dict[str, Any]:
        login = login_result.get("result", {})
        accounts = accounts_result.get("result", {}).get("accounts", [])
        repo = repo_result.get("result", {})
        visible = repo.get("repository_full_name") == target
        permissions = repo.get("permissions") or {}
        return {
            "authenticated": bool(login.get("login")),
            "app_installed": any(a.get("login") == login.get("login") for a in accounts),
            "repository_visible": visible,
            "writable": permissions.get("push") is True,
            "repository": repo.get("repository_full_name"),
            "default_branch": repo.get("default_branch"),
        }
