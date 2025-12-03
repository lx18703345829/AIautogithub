# 自动解析 GitHub 项目的本地部署应用（跨平台，Mac ARM 优先）PRD + 技术方案

## 【一】产品目标 / 用户价值
- 目标：用户输入 GitHub 地址（public/private），系统自动解析项目类型与依赖、生成本地部署步骤、在用户确认后自动执行，并全程提供状态展示、错误检测、自愈与失败原因可视化。
- 痛点：开源项目环境复杂（语言/版本/GPU/系统差异）、依赖冲突、文档不完整、跨平台兼容差、错误定位困难。
- 典型用户：
  - AI/Python 工程师：快速拉起推理项目（Whisper/Llama/R1 等）
  - PM/数据科学家：无需了解环境细节即可试用 Demo
  - 开源项目体验者与创业团队：快速验证与对比多个仓库

## 【二】用户完整操作流程（非常详细）
1. 打开应用
   - UI 加载系统能力概览（OS、架构、Python/Node/Docker 是否安装、GPU 可用性、端口状态）。
2. 输入 GitHub 地址
   - 支持粘贴 URL 或登录绑定 GitHub 账户以访问 private 仓库；选择分支/Tag（可选）。
3. 项目拉取与准备
   - 克隆仓库到隔离工作目录；记录 commit/branch；支持断点续传与代理切换。
4. 解析与分析
   - 读取 README、requirements.txt、environment.yml、Dockerfile、package.json、setup.py、pyproject.toml、Makefile、docker-compose.yml 等。
   - 识别项目语言（Node/Python/Java/Go/Rust/Docker/mixed）、版本约束（Python/Node/Java）、依赖集合、运行方式（命令与参数）、硬件需求（CUDA/GPU/CPU/内存）、外部资源（模型/数据文件）。
5. 生成 Deployment Plan
   - 以步骤清单形式输出：环境准备 → 依赖安装 → 资源下载 → 启动命令 → 健康检查 → 可视化入口。
   - 每步包含：前置判断、操作、回滚、错误分类与修复策略、重试机制。
6. 用户确认执行
   - 显示预计耗时与资源占用；需要权限的步骤给出权限说明与原因。
7. 自动执行
   - 实时日志输出（按步骤流与时间线）；错误即时可视化；支持“一键修复并重试”。
8. 部署成功
   - 展示可用端口、Web UI 地址、启动/停止命令、环境信息（Python/Node 版本、依赖快照）。
9. 失败处理
   - 显示失败原因、已尝试修复操作、下一步建议；支持导出诊断报告与操作复盘。

## 【三】核心功能模块（详细：输入/输出/逻辑/错误/修复）
1. GitHub 地址解析模块
   - 输入：`repo_url`、`branch/tag`、`auth_token(可选)`
   - 输出：`clone_path`、`repo_meta(commit, branch)`
   - 处理逻辑：校验 URL 格式 → 选择拉取方式（git/gh API）→ 处理私有仓库权限 → 断网/慢网重试 → 代理切换。
   - 可能错误：认证失败/速率限制/网络不稳定/仓库不存在。
   - 修复：提示登录或 PAT；指数退避重试；切换镜像/代理；校验 URL 并给出示例。

2. 项目结构分析模块
   - 输入：`clone_path`
   - 输出：`ProjectSpec(language, versions, deps, start_commands, gpu/cpu/mem, arm_supported, needs_resources)`
   - 逻辑：解析 README/requirements/environment.yml/Dockerfile/package.json/setup.py/pyproject.toml/docker-compose.yml/Makefile；提取语言与运行命令；抽取版本约束与依赖；GPU/CUDA/Metal 关键词与 API 检测。
   - 错误：文件缺失/格式异常/解析失败。
   - 修复：多文件回退策略（pyproject→setup→requirements）；宽松解析（容错 JSON/TOML）；基于 README 的命令抽取补全。

3. 环境需求识别模块
   - 输入：`ProjectSpec`、系统能力（OS、arch、已安装工具）
   - 输出：`EnvNeeds(python/node/java versions, system deps, docker need, gpu need)`
   - 逻辑：匹配版本约束；判断 ARM 兼容性；识别需要的系统依赖（brew/apt/choco）；GPU 检测（CUDA/Metal/加速库）。
   - 错误：系统缺组件/版本不满足/架构不兼容。
   - 修复：自动安装 Xcode CLT/Homebrew/pyenv/nvm；创建 venv；提示 Rosetta（Intel 二进制）；GPU 不可用时切 CPU。

4. 自动生成 Deployment Plan 模块
   - 输入：`ProjectSpec`、`EnvNeeds`
   - 输出：`DeploymentPlan(steps[])`，每步包含：`precheck/actions/rollback/errors/fixes/retry`
   - 逻辑：将环境准备、依赖安装、资源下载、启动命令、健康检查编排为可执行、可回滚的流程；端口选择策略；日志打点。
   - 错误：计划不可执行/缺少关键信息。
   - 修复：向用户确认缺失参数（例如模型文件路径）；提供默认值与安全替代（CPU 模式、通用端口）。

5. 自动执行引擎（实时日志）
   - 输入：`DeploymentPlan`
   - 输出：`RunState(status per step, logs, artifacts)`
   - 逻辑：逐步执行，步骤间支持并发（依赖安装可并行）；每步产生结构化日志事件；失败触发修复策略与重试；最终产出可访问入口。
   - 错误：命令失败/超时/权限不足/磁盘不足。
   - 修复：重试（指数退避）；请求权限；清理缓存；提示磁盘空间；分步执行并允许跳过非关键步骤。

6. 错误分类与自动修复引擎
   - 输入：`logs`、`system capability`、`ProjectSpec`
   - 输出：`Diagnosis(category, reason, suggested_fix, risk_level)`
   - 逻辑：基于正则与模式库识别：环境类/依赖类/资源类/运行时类；生成 N 条修复策略，按安全度排序自动执行首选；支持回滚与多次重试。
   - 错误：误判/修复不可用/二次错误。
   - 修复：回滚上一操作；切换到更保守策略；提示用户手动方案并可一键执行。

7. 系统能力检测（显卡、CPU、依赖、端口等）
   - 输入：系统信息（OS/arch/CPU/GPU/内存/磁盘/端口）
   - 输出：`Capabilities(gpu_available, metal/cuda, installed tools, free_ports, disk space)`
   - 逻辑：调用系统命令/库检测；端口扫描；GPU 能力与驱动；工具链版本。
   - 错误：检测失败/信息不全。
   - 修复：回退到最小集；提示用户补装；提供脚本一键安装。

8. 跨平台支持层（Mac ARM 必须具体到实现）
   - 输入：`Capabilities`、`EnvNeeds`
   - 输出：平台特定执行策略（安装命令、路径、权限）
   - 逻辑：
     - macOS ARM：
       - 包管理：Homebrew（/opt/homebrew），自动安装与镜像源；Xcode CLT 检测与安装。
       - Python：`pyenv`/`venv`/`uv`；创建 `python3.10+` venv；`pip` 源切换（如清华）。
       - Node：`nvm` 切换；`npm ci` 并行；`universal2` 轮子优先。
       - GPU：Metal/accelerate；检测 CUDA 不可用时自动 CPU 模式；为 PyTorch 选择 `torch>=2` + `mps` 后端。
       - 端口：扫描占用并选择可用端口；冲突时自动递增。
     - macOS Intel：支持 Rosetta 与 Intel 路径；brew 为 `/usr/local`。
     - Linux：检测发行版（Debian/Ubuntu/RHEL/Arch）；选择 `apt/yum/pacman`；CUDA/ROCm 可选。
     - Windows：`choco/scoop`；PowerShell 执行；建议使用 WSL2 扩展 Linux 路径。
   - 错误：包管理器缺失/权限不足/镜像不通。
   - 修复：自动安装包管理器；sudo 提示与最小权限执行；切换镜像源与代理。

9. Web UI（localhost）可视化交互界面
   - 输入：步骤状态事件、日志、诊断报告、操作命令
   - 输出：仪表盘（待执行/执行中/成功/失败/自愈）、错误面板、一键修复/重试按钮、成功后的入口卡片。
   - 逻辑：本地 Web 服务（端口 5173/3000/8000 可选）；WebSocket 实时日志；事件驱动状态图；可复制诊断报告。
   - 错误：UI 无法启动/端口占用。
   - 修复：自动换端口；提供 CLI 查看与导出。

10. 安全与权限控制
   - 输入：需要权限的操作列表（安装/写文件/网络）
   - 输出：权限请求弹窗、审计日志、操作白名单/黑名单。
   - 逻辑：最小权限原则；敏感操作需解释原因；命令白名单；沙盒目录隔离；secret 使用系统钥匙串；日志脱敏。
   - 错误：权限拒绝/安全策略阻断。
   - 修复：降级方案（不安装系统级，只用用户级）；指导手动授权；回滚改动。

## 【四】全流程失败点与自愈方案清单
- 系统版本不支持/架构不匹配：提示版本要求；Mac Intel→Rosetta；Linux 发行版适配；Win→WSL2 建议。
- 缺少 XCode/Homebrew/Python/Node/Docker：自动检测与安装；需要时提示授权与原因；重试与镜像切换。
- 权限不足：解释操作目的与影响；请求提升；失败则降级执行或提示手动步骤。
- Git clone 失败：指数退避重试；切换代理/镜像；断点续传；给出错误码说明。
- 依赖安装失败：更换 pip 源；尝试 `universal2` 轮子；并行安装与失败隔离；版本降级/升级；缺失 brew 包自动补装。
- Docker 缺失：提示安装与引导；提供非 Docker 路径运行（venv/uv）。
- 项目需要 GPU：检测 GPU；Mac→MPS/Metal；无 GPU→CPU 模式并提示性能影响。
- 端口被占用：自动换端口并更新启动命令；记录变更供用户复制。
- 资源不足（磁盘/内存）：提示释放空间/限制并发；缓存清理；分步下载。
- 运行时错误（import/module not found）：自动安装缺依赖；修复版本冲突；重试后仍失败给出详细日志定位。

## 【五】最终输出内容（落地说明）
1. 完整 PRD：本文件，并已拆分模块与输入输出。
2. 技术架构图说明（文字）：
   - Orchestrator（流程调度）居中，连接 RepoParser、EnvManager、ErrorEngine、Runner、HealthCheck、LogEngine；UI 通过事件消费状态。
   - 数据流：Git 拉取→解析→生成计划→环境准备→依赖安装→资源下载→启动→健康检查→错误引擎→自愈/重试→UI 展示。
3. 模块交互流程说明：
   - 用户输入→Orchestrator 调用 Git 模块→解析模块输出 ProjectSpec→环境模块生成 RunPlan→执行引擎按计划执行→健康检查回传→错误引擎诊断并修复→日志引擎持续输出事件→UI 更新状态与提供操作。
4. 跨平台实现策略（重点 Mac ARM）：见模块 8，包含包管理选择、路径、GPU 策略、端口与权限方案。
5. 错误识别与自愈系统详细设计：
   - 分类：环境/依赖/资源/运行时；模式库与规则优先级；修复动作安全分级（可回滚/需确认/高风险禁用）。
   - 重试：指数退避、最大次数、成功阈值；失败收敛策略（降级/跳过非关键步骤）。
   - 报告：生成结构化诊断 JSON，支持导出与复制。
6. 详细日志系统设计：
   - 事件模型：`step_started/step_succeeded/step_failed/fix_applied/retry`；包含时间戳、步骤 ID、命令、摘要、关联 ID。
   - 分级：DEBUG/INFO/WARN/ERROR；结构化 JSON 输出；本地持久化与旋转；敏感信息脱敏。
   - UI：实时流展示、筛选、复制；失败高亮与修复入口。
7. 可执行的 MVP 范围：
   - 支持 Git 拉取（public/private PAT）与解析（Python/Node/Docker 基本识别）。
   - 生成 Deployment Plan（venv/uv + `pip install` + `npm install` + `docker-compose up` 三类）。
   - 执行引擎串行 + 部分并行安装；端口检测与自动切换；Web UI 显示进度与错误。
   - 自愈策略基础版：pip 源切换、版本降级、CPU 模式、端口重选、重试机制。
8. 未来可扩展方向：
   - 插件系统（语言/框架适配器：Java/Maven、Go、Rust/Cargo、Conda）。
   - 团队共享配置与云端运行分析；远程缓存与构建加速。
   - 更智能的错误诊断（LLM 辅助建议并安全评审）。

## 实施建议与里程碑
- V1（4–6 周）：Git 拉取、解析器（Python/Node/Docker）、Deployment Plan、基础执行引擎、错误可视化、自愈基础版、Web UI 日志。
- V2（6–8 周）：完善跨平台层、系统能力检测、并发安装与缓存、GPU/MPS 支持、更多修复策略、报告导出。
- V3（8–10 周）：插件生态、团队共享、云端分析、LLM 辅助诊断与修复。

## 统一数据契约（供前后端与 CLI 共享）
```json
{
  "project": {
    "name": "string",
    "language": "python|node|java|go|rust|docker|mixed",
    "python_required": "string|null",
    "node_required": "string|null",
    "java_required": "string|null",
    "gpu_required": false,
    "arm_supported": true,
    "dependencies": ["string"],
    "start_commands": ["string"],
    "resources": ["models|data|config"]
  },
  "plan": {
    "env_type": "venv|uv|docker",
    "install_steps": ["string"],
    "fixups": ["string"],
    "ports": ["number"]
  },
  "diagnostics": [
    {"category": "env|dep|resource|runtime", "message": "string", "suggestion": "string", "risk": "low|medium|high"}
  ],
  "logs": [{"ts": "ISO", "level": "INFO", "event": "step_started", "step_id": "string", "summary": "string"}]
}
```

---
注：本 PRD + 技术方案已与仓库原型对齐，解析器与 CLI 原型位于 `src/autodeploy/`，可作为 MVP 的基础实现接口与数据结构参考。

