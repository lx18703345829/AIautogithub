from typing import List

from .models import RunPlan, ProjectSpec


def plan_environment(spec: ProjectSpec) -> RunPlan:
    env_type = "venv"
    fixups: List[str] = []
    if spec.python_required:
        fixups.append(f"创建 Python {spec.python_required} 虚拟环境")
    if spec.node_required:
        fixups.append(f"切换 Node 版本到 {spec.node_required}")
    if spec.gpu_required and spec.arm_supported is False:
        fixups.append("切换到 CPU 模式并替换不兼容依赖")
    install_steps: List[str] = []
    if spec.dependencies:
        install_steps.append("pip 安装 requirements.txt 依赖")
    return RunPlan(env_type=env_type, install_steps=install_steps, fixups=fixups)

