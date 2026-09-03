"""Shared data models for the system."""
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Evidence:
    source: str
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Solution:
    summary: str
    actions: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    verified: bool = False
