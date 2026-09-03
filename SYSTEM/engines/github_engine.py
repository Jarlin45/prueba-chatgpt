"""GitHub engine interface for collecting access evidence.

The engine is deliberately provider-agnostic: the orchestrator supplies context,
and a future adapter can connect the checks to GitHub APIs or the local CLI.
"""
from typing import Any, Dict


class GitHubEngine:
    name = "github"

    def check_access(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate supplied GitHub access evidence.

        Expected context keys can include: authenticated, app_installed,
        repository_visible, writable. No network calls are made here.
        """
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
