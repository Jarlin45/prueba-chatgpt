"""Evidence analysis layer.

Interprets repository evidence against the active problem type. It does not
change files and does not claim a root cause unless the evidence supports it.
"""
from collections import defaultdict
from hashlib import sha256
from typing import Any, Dict, List


class EvidenceAnalyzer:
    name = "evidence-analysis"

    def analyze(self, problem: str, problem_type: str, inspection: Dict[str, Any]) -> Dict[str, Any]:
        files = {
            item.get("path"): item
            for item in inspection.get("inspected_paths", [])
            if item.get("type") == "file"
        }
        directories = {
            item.get("path"): item
            for item in inspection.get("inspected_paths", [])
            if item.get("type") == "directory"
        }

        findings: List[Dict[str, Any]] = []

        # Detect duplicate filenames across inspected directories. A duplicate
        # is not automatically a runtime conflict: relevance of each path is
        # evaluated before assigning severity.
        by_name = defaultdict(list)
        for path, item in files.items():
            by_name[path.rsplit("/", 1)[-1]].append(item)

        if problem_type == "repository_structure":
            for filename, items in by_name.items():
                if len(items) < 2:
                    continue
                findings.append(self._duplicate_finding(filename, items))

            findings.append({
                "type": "structure",
                "severity": "info",
                "message": "La estructura raíz y las rutas seleccionadas fueron inspeccionadas.",
                "evidence": ["repository_root"] + list(files.keys()) + list(directories.keys()),
            })
        elif problem_type == "deployment":
            if "vercel.json" in files:
                findings.append(self._vercel_config(files["vercel.json"]))
            else:
                findings.append({
                    "type": "evidence_gap", "severity": "low",
                    "message": "No se encontró vercel.json; el despliegue puede usar configuración por defecto.",
                    "evidence": [],
                })
            if "api" in directories:
                findings.append({
                    "type": "evidence", "severity": "info",
                    "message": "Existe un directorio api en la raíz del repositorio.",
                    "evidence": ["api"],
                })
        elif problem_type == "frontend_api":
            frontend = files.get("index.html")
            api = files.get("api/diagnose.py")
            if frontend:
                text = frontend.get("content", "")
                findings.append({
                    "type": "evidence", "severity": "info",
                    "message": "Se encontró la interfaz raíz y su contenido puede analizarse para detectar llamadas al API.",
                    "evidence": ["index.html"],
                    "signals": {"fetch_present": "fetch(" in text, "post_present": "method:'POST'" in text or 'method:"POST"' in text},
                })
            if api:
                text = api.get("content", "")
                findings.append({
                    "type": "evidence", "severity": "info",
                    "message": "Se encontró el endpoint /api/diagnose.py.",
                    "evidence": ["api/diagnose.py"],
                    "signals": {"post_handler_present": "def do_POST" in text, "diagnose_present": "def diagnose" in text},
                })
        elif problem_type == "github_access":
            if inspection.get("repository"):
                findings.append({
                    "type": "evidence", "severity": "info",
                    "message": "El motor pudo inspeccionar el repositorio mediante la API de GitHub.",
                    "evidence": ["repository_root"],
                })
        else:
            findings.append({
                "type": "evidence", "severity": "info",
                "message": "Se obtuvo evidencia inicial de la estructura y archivos seleccionados.",
                "evidence": list(files.keys()) + list(directories.keys()),
            })

        skipped = inspection.get("skipped_paths", [])
        if skipped:
            findings.append({
                "type": "evidence_gap", "severity": "info",
                "message": "Algunas evidencias solicitadas no estaban disponibles y fueron marcadas como omitidas.",
                "evidence": [item.get("path") for item in skipped],
            })

        return {
            "analyzer": self.name,
            "problem_type": problem_type,
            "finding_count": len(findings),
            "findings": findings,
            "root_cause_confirmed": False,
            "analysis_status": "evidence_interpreted",
        }

    def _duplicate_finding(self, filename: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        paths = [item.get("path") for item in items]
        hashes = [sha256(item.get("content", "").encode("utf-8")).hexdigest() for item in items]
        identical = len(set(hashes)) == 1

        relevance = [self._path_relevance(path, filename) for path in paths]
        conflict_likelihood = "high" if sum(level == "high" for level in relevance) >= 2 else "low"

        if filename == "README.md":
            severity = "info"
            assessment = "La duplicación es documental y normalmente no afecta la ejecución."
        elif identical:
            severity = "low" if conflict_likelihood == "low" else "medium"
            assessment = "El contenido es idéntico; parece una copia redundante y no demuestra por sí solo un conflicto."
        elif conflict_likelihood == "high":
            severity = "high"
            assessment = "Ambas rutas parecen relevantes para ejecución/configuración; el contenido difiere y requiere revisión."
        else:
            severity = "medium"
            assessment = "El contenido difiere, pero solo una de las rutas parece relevante para ejecución; no se demuestra un conflicto."

        return {
            "type": "duplicate_filename",
            "severity": severity,
            "message": f"Se encontraron {len(items)} archivos llamados {filename} en rutas distintas. {assessment}",
            "evidence": paths,
            "signals": {
                "content_identical": identical,
                "path_relevance": dict(zip(paths, relevance)),
                "conflict_likelihood": conflict_likelihood,
            },
        }

    def _path_relevance(self, path: str, filename: str) -> str:
        """Estimate whether a path is likely to participate in execution.

        This is deliberately conservative: it is a structural signal, not a
        claim about the deployment platform's actual routing behavior.
        """
        if path == filename:
            return "high"
        if path.startswith("api/"):
            return "high"
        if path.startswith("SYSTEM/"):
            return "low"
        return "medium"

    def _vercel_config(self, item: Dict[str, Any]) -> Dict[str, Any]:
        text = item.get("content", "")
        runtime_present = '"runtime"' in text or "'runtime'" in text
        return {
            "type": "configuration",
            "severity": "warning" if runtime_present else "info",
            "message": (
                "vercel.json contiene una configuración explícita de runtime; requiere revisión."
                if runtime_present else "vercel.json no declara un runtime explícito."
            ),
            "evidence": ["vercel.json"],
            "signals": {"runtime_present": runtime_present},
        }
