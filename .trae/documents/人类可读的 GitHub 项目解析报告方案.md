## 输出目标

* 为指定 GitHub 仓库生成人类可读的“项目解析报告”，避免任何纯 JSON 或复杂嵌套结构。

* 报告包含：项目名称、主要功能、使用语言与依赖、主要文件与目录结构（简明）、启动/运行方式。

## 数据来源与解析范围

* 读取并解析以下文件（若存在）：README、package.json、requirements.txt、pyproject.toml、setup.py、Dockerfile、docker-compose.yml、Makefile、Procfile、主入口文件（main.py/app.py/index.js等）。

* 辅助判断：根据 README 的“运行”或“启动”章节抽取命令；根据 scripts/start、python 入口与 docker-compose 服务推断运行方式。

## 语言与依赖识别

* Node/JS：package.json 的 dependencies/devDependencies 与 scripts；Vite/Next/Nuxt 等框架识别。

* Python：requirements.txt、pyproject.toml 的 requires-python 与依赖；入口文件（main.py/app.py）。

* 其他语言：

  * Go：go.mod（module、require）与 main.go。

  * Rust：Cargo.toml（package、dependencies）与 src/main.rs。

  * Java：pom.xml/gradle.build；Spring Boot 端口与入口。

* Docker：Dockerfile 基础镜像、ENTRYPOINT/CMD；docker-compose 服务与端口。

## 运行方式识别

* 优先读取：

  * Node：`npm run dev`/`npm start`、框架默认端口（如 3000）。

  * Python：`python main.py`、`uvicorn app:app --port 8000`。

  * Docker：`docker-compose up` 或 `docker run` 命令。

* 若未显式给出，结合 README、框架约定与文件结构给出合理推断，并标注“可能值”

## 输出格式（人类可读）

* 标题：项目名称

* 列表/简表：

  * 主要功能（3–6条）

  * 使用语言与依赖（按语言分组，列出核心依赖 5–10 个）

  * 主要文件与目录（1–2层，简明解释作用）

  * 启动/运行（分平台或通用命令，直接可复制）

* 说明：若某项缺失或不确定，明确标注“未找到/待确认”。

## 边界与健壮性

* 私有仓库：若无法读取，提示需凭证；报告以可读取信息为主。

* 超大仓库：仅解析关键文件与根目录；结构说明保持简洁。

* 冲突信息：若多处给出不同启动方式，按优先级（scripts→README→Docker）给出首选与备选。

## 交付示例结构（示意）

* 项目名称：<name>

* 主要功能：

  * 功能A（一句话）

  * 功能B（一句话）

* 使用语言与依赖：

  * Node：react、next、axios …

  * Python：fastapi、uvicorn …

* 主要文件与目录：

  * /app：主页面与路由

  * /components：通用组件

  * Dockerfile：镜像构建与启动命令

* 启动/运行：

  * 通用：`npm install && npm run dev`，`http://localhost:3000`

  * Python：`pip install -r requirements.txt && uvicorn app:app --port 8000`

## 执行说明

* 请提供 GitHub 仓库链接后，我将按上述方案解析并输出人类可读的报告（不含任何纯 JSON）。

