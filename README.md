# AIautogithub

自动解析 GitHub 项目并一键本地部署的 Mac ARM 应用原型（TRUE 团队增强版）。

## 快速开始
- 运行测试：`python3 -m unittest discover -s tests -q`
- 生成报告：`python3 -m src.autodeploy.cli --path tests/fixtures/sample_repo --output report.json`

## 目录结构
- `docs/PRD-v2.md`：产品方案 v2
- `docs/tech-design.md`：技术设计
- `docs/architecture.md`：架构与数据流
- `src/autodeploy/`：解析器、环境计划、错误引擎与 CLI
- `tests/`：单元测试与示例仓库

## 功能概览
- 解析 README、requirements、Dockerfile、package.json、setup.py、pyproject.toml
- 检测 Python/Node 版本、GPU/CUDA 需求、ARM 兼容性
- 提取启动命令并生成运行计划
- 输出统一 JSON 报告，供 UI 展示与后续编排

## 下一步
- 接入 SwiftUI/Electron UI，展示进度与错误自愈入口
- 扩展自愈策略：pip 源切换、universal2 轮子、brew 依赖检测
- 健康检查与端口自动切换
