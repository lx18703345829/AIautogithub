from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ProjectSpec:
    name: str
    language: str
    python_required: Optional[str]
    node_required: Optional[str]
    gpu_required: bool
    arm_supported: Optional[bool]
    dependencies: List[str]
    start_commands: List[str]


@dataclass
class ParseResult:
    files_found: Dict[str, bool]
    warnings: List[str]
    suggestions: List[str]


@dataclass
class RunPlan:
    env_type: str
    install_steps: List[str]
    fixups: List[str]


@dataclass
class ErrorDiagnosis:
    category: str
    message: str
    suggestion: str
    details: Dict[str, Any] = field(default_factory=dict)

