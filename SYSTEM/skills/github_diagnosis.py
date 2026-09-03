"""First real skill: diagnose basic GitHub access problems."""


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
