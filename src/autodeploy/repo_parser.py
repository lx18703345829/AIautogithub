import json
import os
import re
from typing import List, Optional, Dict

from .models import ProjectSpec, ParseResult


def _read(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def _exists(root: str, name: str) -> bool:
    return os.path.exists(os.path.join(root, name))


def _parse_requirements(text: str) -> List[str]:
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        lines.append(s)
    return lines


def _parse_python_required_from_pyproject(text: str) -> Optional[str]:
    m = re.search(r"requires-python\s*=\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else None


def _parse_python_required_from_setup(text: str) -> Optional[str]:
    m = re.search(r"python_requires\s*=\s*['\"]([^'\"]+)['\"]", text)
    return m.group(1) if m else None


def _parse_node_required_from_package_json(text: str) -> Optional[str]:
    try:
        data = json.loads(text)
    except Exception:
        return None
    engines = data.get("engines")
    if isinstance(engines, dict):
        node = engines.get("node")
        return str(node) if node else None
    return None


def _parse_start_commands(root: str, readme_text: Optional[str], package_json_text: Optional[str]) -> List[str]:
    cmds: List[str] = []
    if package_json_text:
        try:
            data = json.loads(package_json_text)
            scripts = data.get("scripts", {})
            start = scripts.get("start")
            if isinstance(start, str):
                cmds.append("npm start")
        except Exception:
            pass
    for name in ["main.py", "app.py"]:
        if _exists(root, name):
            cmds.append(f"python {name}")
    if _exists(root, "docker-compose.yml"):
        cmds.append("docker-compose up")
    if readme_text:
        for pat in [r"uvicorn\s+\S+:\S+", r"python\s+\S+\.py", r"npm\s+start", r"docker-compose\s+up"]:
            for m in re.finditer(pat, readme_text):
                cmd = m.group(0)
                if cmd not in cmds:
                    cmds.append(cmd)
    return cmds


def _detect_gpu_required(texts: List[str]) -> bool:
    joined = "\n".join([t for t in texts if t])
    keywords = ["cuda", "cudnn", "nvidia", "gpu", "rocm"]
    for k in keywords:
        if re.search(rf"\b{k}\b", joined, flags=re.IGNORECASE):
            return True
    return False


def _detect_arm_support(requirements: List[str], dockerfile_text: Optional[str]) -> Optional[bool]:
    arm_friendly = ["universal2", "apple", "metal"]
    arm_risky = ["tensorflow==", "torch==", "jax==", "nvidia-", "cupy"]
    for r in requirements:
        for k in arm_risky:
            if k in r.lower():
                return False
    if dockerfile_text and re.search(r"arm64|aarch64", dockerfile_text, re.IGNORECASE):
        return True
    for k in arm_friendly:
        if any(k in r.lower() for r in requirements):
            return True
    return None


def parse_project(root: str) -> (ProjectSpec, ParseResult):
    files = {
        "README.md": _exists(root, "README.md"),
        "requirements.txt": _exists(root, "requirements.txt"),
        "environment.yml": _exists(root, "environment.yml"),
        "Dockerfile": _exists(root, "Dockerfile"),
        "package.json": _exists(root, "package.json"),
        "setup.py": _exists(root, "setup.py"),
        "pyproject.toml": _exists(root, "pyproject.toml"),
        "docker-compose.yml": _exists(root, "docker-compose.yml"),
    }

    readme_text = _read(os.path.join(root, "README.md")) if files["README.md"] else None
    req_text = _read(os.path.join(root, "requirements.txt")) if files["requirements.txt"] else None
    env_text = _read(os.path.join(root, "environment.yml")) if files["environment.yml"] else None
    dockerfile_text = _read(os.path.join(root, "Dockerfile")) if files["Dockerfile"] else None
    package_json_text = _read(os.path.join(root, "package.json")) if files["package.json"] else None
    setup_text = _read(os.path.join(root, "setup.py")) if files["setup.py"] else None
    pyproject_text = _read(os.path.join(root, "pyproject.toml")) if files["pyproject.toml"] else None

    requirements = _parse_requirements(req_text) if req_text else []

    python_required = None
    if pyproject_text:
        python_required = _parse_python_required_from_pyproject(pyproject_text)
    if not python_required and setup_text:
        python_required = _parse_python_required_from_setup(setup_text)
    node_required = _parse_node_required_from_package_json(package_json_text) if package_json_text else None

    gpu_required = _detect_gpu_required([readme_text or "", dockerfile_text or ""]) or False
    arm_supported = _detect_arm_support(requirements, dockerfile_text)

    start_commands = _parse_start_commands(root, readme_text, package_json_text)

    language = "mixed"
    if package_json_text and not req_text:
        language = "node"
    elif req_text and not package_json_text:
        language = "python"
    elif dockerfile_text and not req_text and not package_json_text:
        language = "docker"

    name = os.path.basename(os.path.abspath(root))

    warnings: List[str] = []
    suggestions: List[str] = []
    if gpu_required and arm_supported is False:
        suggestions.append("检测到 GPU 需求且可能不支持 ARM，建议切换 CPU 模式")
    if python_required and not re.match(r"^>=?\s*3\.[0-9]+", python_required):
        warnings.append("未识别 Python 版本约束或格式不标准")
    if not start_commands:
        suggestions.append("未发现启动命令，建议在 README 或 package.json 中提供")

    spec = ProjectSpec(
        name=name,
        language=language,
        python_required=python_required,
        node_required=node_required,
        gpu_required=gpu_required,
        arm_supported=arm_supported,
        dependencies=requirements,
        start_commands=start_commands,
    )

    result = ParseResult(files_found=files, warnings=warnings, suggestions=suggestions)
    return spec, result

