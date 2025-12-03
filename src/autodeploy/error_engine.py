import re
from typing import List

from .models import ErrorDiagnosis


def classify(log: str) -> List[ErrorDiagnosis]:
    ds: List[ErrorDiagnosis] = []
    if re.search(r"Python\s*>=\s*3\.[0-9]+\s*required", log, re.IGNORECASE):
        ds.append(ErrorDiagnosis(category="env", message="Python 版本不足", suggestion="创建对应 Python 虚拟环境并重试"))
    if re.search(r"ModuleNotFoundError|No module named", log):
        ds.append(ErrorDiagnosis(category="dep", message="缺少依赖包", suggestion="重新安装依赖或修复版本冲突"))
    if re.search(r"EADDRINUSE|address already in use|port\s*\d+\s*in use", log, re.IGNORECASE):
        ds.append(ErrorDiagnosis(category="resource", message="端口占用", suggestion="切换到可用端口"))
    if re.search(r"CUDA|NVIDIA", log, re.IGNORECASE):
        ds.append(ErrorDiagnosis(category="env", message="GPU 环境不可用", suggestion="切换 CPU 模式或安装兼容包"))
    return ds

