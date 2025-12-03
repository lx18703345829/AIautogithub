# AIautogithub

自动解析 GitHub 项目并一键本地部署的 Mac ARM 应用原型（TRUE 团队增强版）。

## 快速开始
- 运行测试：`python3 -m unittest discover -s tests -q`
- 生成报告：`python3 -m src.autodeploy.cli --path tests/fixtures/sample_repo --output report.json`

## 启动与使用
- 依赖：`python3`（建议 3.10+）。可选：`git`。
- 分析任意 GitHub 仓库（public）：
  - `git clone <repo_url> repo`
  - `python3 -m src.autodeploy.cli --path repo --output report.json`
- 分析私有仓库：
  - 先配置 Git 凭证（SSH 或 PAT），再执行上述命令。
- 查看结果：
  - `cat report.json` 或使用编辑器打开，内含 `project/plan/run/parse` 四部分结构化信息。

## 启动本地 Web 服务
- 启动：`python3 -m src.web.server --port 5173`
- 访问：在浏览器打开 `http://localhost:5173/`
- 使用：输入本地仓库路径或 GitHub 地址，自动分析并展示结构化结果。

## 常见问题
- `python` 命令不存在：使用 `python3`。
- 私有仓库无法拉取：确认已配置 SSH 或 PAT；也可手动下载 ZIP 后指定 `--path`。
- 报告为空或字段缺失：确保仓库包含 README、requirements、package.json 或 pyproject 等文件。

## 目录结构
- `docs/PRD-v2.md`：产品方案 v2
- `docs/PRD-full.md`：完整、可直接进入开发的 PRD + 技术方案
- `docs/tech-design.md`：技术设计
- `docs/architecture.md`：架构与数据流
- `src/autodeploy/`：解析器、环境计划、错误引擎与 CLI
- `src/web/`：本地 Web 服务（无需虚拟环境，直接本地运行）
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
