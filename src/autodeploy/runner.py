from typing import Dict, Any

from .models import ProjectSpec, RunPlan


def build_run(spec: ProjectSpec, plan: RunPlan) -> Dict[str, Any]:
    cmd = spec.start_commands[0] if spec.start_commands else None
    return {
        "env": plan.env_type,
        "fixups": plan.fixups,
        "install": plan.install_steps,
        "start": cmd,
    }

