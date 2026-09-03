"""Deterministic analysis of repository evidence."""
from collections import defaultdict
from hashlib import sha256
from typing import Any, Dict, List


class EvidenceAnalyzer:
    name = "evidence-analyzer"

    def analyze(self, inspection: Dict[str, Any], problem: str = "") -> Dict[str, Any]:
        inspected = inspection.get("inspected_paths", [])
        findings: List[Dict[str, Any]] = []
        signals: List[str] = []
        gaps: List[str] = []

        # Same filename in different directories is a structural signal,
        # not proof by itself of a runtime conflict.
        by_name = defaultdict(list)
        for item in inspected:
            path = item.get("path", "")
            if item.get("type") == "file":
                by_name[path.rsplit("/", 1)[-1]].append(item)

        for filename, items in by_name.items():
            if len(items) < 2:
                continue
            paths = [item.get("path") for item in items]
            hashes = [sha256(item.get("content", "").encode("utf-8")).hexdigest() for item in items]
            identical = len(set(hashes)) == 1
            signals.append("duplicate_filename:" + filename)
            findings.append({
                "source": "evidence",
                "severity": "medium" if identical else "high",
                "type": "duplicate_filename",
                "message": (
                    f"Se encontraron {len(items)} archivos llamados {filename} en rutas distintas. "
                    + ("El contenido es idéntico; podría existir una copia redundante." if identical
                       else "El contenido difiere; requieren revisión para determinar responsabilidades y posibles conflictos.")
                ),
                "evidence": paths,
                "content_identical": identical,
            })

        paths = {item.get("path") for item in inspected}
        if "index.html" in paths and "api/diagnose.py" in paths:
            signals.append("root_ui_and_api_present")
            findings.append({
                "source": "evidence",
                "severity": "info",
                "type": "ui_api_pair",
                "message": "La interfaz raíz y el endpoint principal están presentes en rutas coherentes para Vercel.",
                "evidence": ["index.html", "api/diagnose.py"],
            })

        if inspection.get("skipped_paths"):
            gaps.extend(item.get("path") for item in inspection["skipped_paths"])

        # Never infer a confirmed root cause from a structural signal alone.
        root_cause_confirmed = any(
            finding.get("type") == "runtime_conflict_confirmed" for finding in findings
        )

        return {
            "status": "evidence_interpreted",
            "findings": findings,
            "signals": signals,
            "evidence_gaps": gaps,
            "root_cause_confirmed": root_cause_confirmed,
            "verification": True,
        }
