import unittest
from unittest.mock import patch

from SYSTEM.core.evidence_analyzer import EvidenceAnalyzer
from SYSTEM.engines.github_engine import GitHubEngine
from SYSTEM.skills.github_diagnosis import GitHubDiagnosisSkill


class TestLayers1to5(unittest.TestCase):
    def setUp(self):
        self.skill = GitHubDiagnosisSkill()
        self.analyzer = EvidenceAnalyzer()

    def test_t1_frontend_api(self):
        plan = self.skill.plan_evidence("La interfaz carga pero el botón no obtiene respuesta del API")
        self.assertEqual(plan["problem_type"], "frontend_api")
        self.assertIn("index.html", plan["evidence_plan"])
        self.assertIn("api/diagnose.py", plan["evidence_plan"])

    def test_t2_deployment(self):
        plan = self.skill.plan_evidence("El proyecto funciona localmente pero falla al desplegarse en Vercel")
        self.assertEqual(plan["problem_type"], "deployment")
        self.assertIn("vercel.json", plan["evidence_plan"])
        self.assertIn("api", plan["evidence_plan"])

    def test_t3_github_access(self):
        plan = self.skill.plan_evidence("El sistema no puede acceder al repositorio de GitHub")
        self.assertEqual(plan["problem_type"], "github_access")
        result = GitHubEngine().check_access({
            "authenticated": True,
            "app_installed": False,
            "repository_visible": False,
        })
        self.assertFalse(result["ok"])
        self.assertEqual(result["severity"], "medium")

    def test_t4_repository_structure_duplicate_analysis(self):
        inspection = {
            "repository": "Jarlin45/prueba-chatgpt",
            "inspected_paths": [
                {"path": "SYSTEM/api/diagnose.py", "type": "file", "content": "system version"},
                {"path": "api/diagnose.py", "type": "file", "content": "runtime version"},
                {"path": "SYSTEM/README.md", "type": "file", "content": "docs"},
                {"path": "README.md", "type": "file", "content": "root docs"},
            ],
            "skipped_paths": [],
        }
        result = self.analyzer.analyze("Hay archivos duplicados y posibles conflictos de estructura", "repository_structure", inspection)
        findings = result["findings"]
        diagnose = next(f for f in findings if "diagnose.py" in f.get("message", ""))
        readme = next(f for f in findings if "README.md" in f.get("message", ""))
        self.assertEqual(diagnose["severity"], "medium")
        self.assertEqual(readme["severity"], "info")
        self.assertFalse(result["root_cause_confirmed"])

    def test_t5_general_does_not_invent_cause(self):
        plan = self.skill.plan_evidence("La aplicación funciona algunas veces y otras veces falla")
        self.assertEqual(plan["problem_type"], "general")
        result = self.analyzer.analyze("La aplicación funciona algunas veces y otras veces falla", "general", {
            "inspected_paths": [], "skipped_paths": []
        })
        self.assertFalse(result["root_cause_confirmed"])

    def test_t6_missing_evidence_is_gap(self):
        result = self.analyzer.analyze("problema estructural", "repository_structure", {
            "inspected_paths": [],
            "skipped_paths": [{"path": "missing/path.py", "reason": "not_found"}],
        })
        gap = next(f for f in result["findings"] if f["type"] == "evidence_gap")
        self.assertEqual(gap["severity"], "info")
        self.assertIn("missing/path.py", gap["evidence"])

    def test_t7_engine_respects_selected_evidence(self):
        engine = GitHubEngine()
        calls = []

        def fake_get(url):
            calls.append(url)
            if url.endswith("/contents/"):
                return [
                    {"name": "index.html", "path": "index.html", "type": "file"},
                    {"name": "api", "path": "api", "type": "dir"},
                ]
            if url.endswith("/contents/index.html"):
                return {"path": "index.html", "type": "file", "size": 1, "sha": "x", "content": "root"}
            raise AssertionError("Unexpected evidence request: " + url)

        with patch.object(engine, "_get", side_effect=fake_get):
            result = engine.inspect_repository("owner/repo", ["index.html"], recursive=False)
        inspected = [item["path"] for item in result["inspected_paths"]]
        self.assertEqual(inspected, ["index.html"])
        self.assertFalse(any("api" in call for call in calls[1:]))

    def test_t8_analyzer_interprets_evidence(self):
        result = self.analyzer.analyze("El botón no obtiene respuesta", "frontend_api", {
            "inspected_paths": [
                {"path": "index.html", "type": "file", "content": "fetch('/api/diagnose', {method:'POST'})"},
                {"path": "api/diagnose.py", "type": "file", "content": "def do_POST(self):\ndef diagnose(problem, repo):"},
            ],
            "skipped_paths": [],
        })
        self.assertEqual(result["analysis_status"], "evidence_interpreted")
        self.assertGreaterEqual(result["finding_count"], 2)

    def test_t9_root_cause_is_not_claimed(self):
        result = self.analyzer.analyze("hay un problema", "general", {
            "inspected_paths": [{"path": "index.html", "type": "file", "content": "anything"}],
            "skipped_paths": [],
        })
        self.assertFalse(result["root_cause_confirmed"])

    def test_t10_structural_regression_priority(self):
        plan = self.skill.plan_evidence(
            "La interfaz carga correctamente, pero quiero verificar archivos duplicados o estructuras que causen conflictos entre SYSTEM/api/diagnose.py y api/diagnose.py."
        )
        self.assertEqual(plan["problem_type"], "repository_structure")
        self.assertEqual(plan["evidence_plan"], ["SYSTEM", "api", "vercel.json", "index.html", "README.md"])


if __name__ == "__main__":
    unittest.main()
