# Ombre Brain 代码健康度审计

审计日期：2026-07-15  
审计分支：`main`  
HEAD：`821a1af42b3ec7993c26cae819c8d7d546663f45`  
工作树口径：包含用户尚未提交的 2.7.1 修复；本阶段除本报告外不修改生产代码、测试或用户数据。

## 第一阶段：代码盘点

### 工程边界与判定口径

本阶段先读取并遵循 `rule.md`、`docs/CLAUDE_PROMPT.md`、`docs/INTERNALS.md`、`docs/OPERATIONS.md`、CI 工作流和上一轮 2026-07-12 审计。记忆 Markdown、`config.yaml`、密钥、缓存、`buckets/` 与 `test_buckets/` 不作为源码扫描输入，也未读取用户真实记忆。

- **活**：生产入口可达、被 FastMCP/Web 动态注册、独立 CLI 有调用入口，或被当前 pytest/构建/交付链实际引用。
- **死**：生产、CLI、测试、文档、注册机制均无消费者，且没有公共兼容契约迹象。
- **存疑**：只有预研测试/架构文档可达，或仅是人工入口/兼容接口；不能仅凭静态扫描删除。
- 装饰器路由、`__getattr__`、`globals().update()`、事件属性、反射和协议方法均按框架真实语义人工复核，不把 Vulture 的动态入口误报当死代码。

### 范围与结果

- 遍历当前 Git 跟踪及未忽略文件 **519** 个；其中 **417** 个代码、测试、配置、静态资源和交付资产逐文件列入下表。101 个 Markdown 文档及许可证等非代码文件用于交叉引用，但不机械判死。
- `src/**` 共 **188** 个 Python 模块、约 41,698 行：172 个从 `src/server.py` 生产入口可达，3 个是独立 CLI/评测库，13 个仅预研测试/架构文档可达，**0 个高置信整文件死模块**。
- 172 个生产可达模块中，35 个只通过 `web.system` 诊断链可达；它们是生产诊断面活代码，不是核心 MCP 请求必经路径。
- Web 注册面：14 个 FastMCP 工具、18 个 `web.register(mcp)` 模块、113 个 `custom_route`。
- pytest：175 个 `test_*.py` 全部被收集，共 **1288** 个测试项；无未收集测试文件。
- 前端：Dashboard 227 个顶层函数建立事件/调用图，2 个旧兼容 wrapper 不可达；onboarding 8 个函数全部可达；3 段 Dashboard inline script 均可编译。
- 文件状态统计：**活 401、死 2、存疑 14**。

### 高置信死文件

| 文件路径 | 状态 | 证据 |
|---|---|---|
| `frontend/RRPL.ttf` | 死 | 3,264,764 字节；仅在静态白名单中列名，HTML/CSS/manifest、文档和测试均不请求，没有 `@font-face`。 |
| `requirements-local.txt` | 死 | 仍描述已移除的 sentence-transformers 后端和不存在的 `INSTALL_LOCAL_EMBED` build arg；当前本地 embedding 明确统一走 Ollama API。 |

### 符号级死代码与冗余状态

| 文件/符号 | 状态 | 说明 |
|---|---|---|
| `src/web/oauth.py::_mcp_auth_check` | 死 | 私有函数仅定义，无装饰器、导出或调用；实际 Bearer 鉴权在 `server_app` 中间件。 |
| `frontend/dashboard.html::renderConceptNetwork` | 死 | 仅定义和注释出现；当前 concept 路径直接调用 `initConceptNetwork`。 |
| `frontend/dashboard.html::drawConceptNetwork` | 死 | 仅定义和注释出现；实际分支调用 `initConceptNetwork` / `drawBucketNetwork`。 |
| `src/bucket_manager.py:291-307 wikilink_*` | 死 | 8 个实例属性只赋值不读取；配置与 INTERNALS 已声明自动注入废弃。 |
| `src/errors.py::ALL_LEVELS` | 死 | 仅定义，无仓内读取。 |
| `src/utils.py::BOOT_ENV_OMBRE` | 死 | 仅定义；当前启动配置使用 `BOOT_ENV_CONFIG`。 |
| `src/github_sync.py::_batch_commit.uploaded` | 死 | 局部计数只写不读，函数最终返回 `len(files)`。 |
| `src/web/buckets.py::import os` | 死 | Ruff F401 唯一生产报告；文件中无 `os` 使用。 |
| `tests/conftest.py::buggy_config/mock_dehydrator/mock_embedding_engine/_write_bucket_file` | 死 | fixture/helper 无任何测试参数或调用引用。 |
| `tests/test_v3_legacy_tools_runtime.py::_async_value/_async_raise` | 死 | 测试私有 helper 仅定义，无调用。 |

### 存疑符号：禁止机械删除

- `BaseEmbeddingEngine.warmup`、`EmbeddingOutbox.process_once`、`LegacyRuntime.debug_decision_health`、`migration_engine.reset_for_test`。
- `ConsensusEngine` Protocol，以及 `ConfigError`、`ClusterUnavailable`、`VectorRebuildError`、`HotUpdateRejected`、`MigrationFailed` 公共错误 taxonomy。
- `web._shared.write_deletion_notice/pop_deletion_notice`：当前只写不读，但源码明确标记为旧扩展兼容注入槽。
- `ErrorSpec.suggestion_en`：仓内未消费，但属于公开错误结构的双语扩展字段。

### 工具交叉验证

- Python AST：188/188 模块解析成功；补齐相对导入与父包后，生产/CLI/测试/文档联合可达集合无孤儿模块。
- Vulture 2.16：80% 阈值无输出；60% 结果主要是 FastMCP 装饰器、路由 handler、dataclass/Enum 和协议方法假阳性。
- Ruff 0.15.21（`F401,F811`）：仅 `src/web/buckets.py:14 import os`；无 F811。
- 前端 Acorn/事件根扫描：227 个顶层函数中仅 2 个不可达，无缺失事件处理器。
- `.dockerignore` 额外发现构建上下文与注释不一致：未排除 Rust `target/`（本地约 20.8MB）、`.coverage`、`test_buckets/` 等；作为第二阶段性能/交付问题处理。

### 逐文件清单

文件路径 | 状态（活/死/存疑） | 说明
---|---|---
`.claude/hooks/session_breath.py` | 活 | 由 .claude/settings.json 的 SessionStart/resume hook 调用。
`.claude/settings.json` | 活 | Claude Code 项目 hook 配置入口。
`.dockerignore` | 活 | 仓库、构建上下文或版本控制行为配置。
`.env.example` | 活 | 用户配置模板与部署契约。
`.gitattributes` | 活 | 仓库、构建上下文或版本控制行为配置。
`.github/workflows/docker-publish.yml` | 活 | GitHub Actions 实际 CI/发布工作流入口。
`.github/workflows/tests.yml` | 活 | GitHub Actions 实际 CI/发布工作流入口。
`.gitignore` | 活 | 仓库、构建上下文或版本控制行为配置。
`config.example.yaml` | 活 | 用户配置模板与部署契约。
`deploy/deploy.sh` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`deploy/docker-compose.multi.yml` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`deploy/docker-compose.testing.yml` | 存疑 | 可手工叠加的本地测试 overlay，但仓库工作流、测试和文档均不调用；保留价值需维护者确认。
`deploy/docker-compose.user.yml` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`deploy/docker-compose.yml` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`deploy/fetch_cloudflared.py` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`deploy/gen_update_manifest.py` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`deploy/multi_owner.py` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`deploy/owners.example.yaml` | 活 | 部署脚本、Compose 配置或用户模板，有文档/测试/构建入口引用。
`Dockerfile` | 活 | 生产构建、启动或平台部署入口。
`entrypoint.sh` | 活 | 生产构建、启动或平台部署入口。
`frontend/dashboard.html` | 活 | Dashboard 主页面，由 web/dashboard.py 提供；事件与脚本入口已建立调用图。
`frontend/favicon.svg` | 活 | Dashboard 静态资源，被页面、manifest 或静态路由消费。
`frontend/icon.svg` | 活 | Dashboard 静态资源，被页面、manifest 或静态路由消费。
`frontend/manifest.json` | 活 | Dashboard 静态资源，被页面、manifest 或静态路由消费。
`frontend/onboarding.html` | 活 | 安全部署向导页面，由 web/onboarding.py 的 /onboarding 路由提供。
`frontend/RRPL.ttf` | 死 | 仅被静态资源白名单允许访问；HTML/CSS/manifest、文档和测试均无消费，3.26MB 孤儿字体资产。
`kernel/rust/ombre-kernel/Cargo.toml` | 活 | Rust 内核脚手架；由 Cargo/pytest 架构验收引用，尚非 Python 生产热路径。
`kernel/rust/ombre-kernel/src/lib.rs` | 活 | Rust 内核脚手架；由 Cargo/pytest 架构验收引用，尚非 Python 生产热路径。
`render.yaml` | 活 | 生产构建、启动或平台部署入口。
`requirements-dev.in` | 活 | 依赖声明/锁文件，由 Docker 或 CI 安装、校验。
`requirements-dev.lock.txt` | 活 | 依赖声明/锁文件，由 Docker 或 CI 安装、校验。
`requirements-local.txt` | 死 | 描述已移除的 sentence-transformers/bge 本地后端与不存在的 Docker build arg；当前本地后端为 Ollama API。
`requirements.lock.txt` | 活 | 依赖声明/锁文件，由 Docker 或 CI 安装、校验。
`requirements.txt` | 活 | 依赖声明/锁文件，由 Docker 或 CI 安装、校验。
`ruff.toml` | 活 | Ruff 本地与 CI 静态检查配置。
`src/backup_archive.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/bm25_index.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/bucket_manager.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/bucket_scoring.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/decay_engine.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/dehydrator.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/deployment_profile.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/embedding_engine.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/embedding_outbox.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/errors.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/github_sync.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/import_memory.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/ledger_mirror.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/ledger_property.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/ledger_replay.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/media_store.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/memory_messages.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/migrate_engine.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/migration_engine.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/ombrebrain/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/acceptance/__init__.py` | 存疑 | 仅 pytest v3 formal-acceptance 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/acceptance/contracts.py` | 存疑 | 仅 pytest v3 formal-acceptance 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/acceptance/harness.py` | 存疑 | 仅 pytest v3 formal-acceptance 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/adapters/__init__.py` | 存疑 | 仅 pytest v3 adapter/migration 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/adapters/bucket_adapter.py` | 存疑 | 仅 pytest v3 adapter/migration 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/adapters/migration.py` | 存疑 | 仅 pytest v3 adapter/migration 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/app/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/command_boundary_health.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/command_bridge.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/execution.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/legacy_runtime.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/legacy_wiring.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/neural_router.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/profiles.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/app/tool_output_contract.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/architecture/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/architecture/adr.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/architecture/auditor.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/architecture/code_standards.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/architecture/contracts.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/architecture/defaults.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/capabilities/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/capabilities/catalog.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/consensus.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/node.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/raft/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/raft/leader.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/raft/log.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/raft/quorum.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/replication/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/replication/apply.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/replication/catchup.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/replication/contract.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/safety/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/cluster/safety/integrity.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/collab/__init__.py` | 存疑 | 仅 pytest v3 collaboration graph 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/collab/graph.py` | 存疑 | 仅 pytest v3 collaboration graph 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/collab/merge_policy.py` | 存疑 | 仅 pytest v3 collaboration graph 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/decision/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/decision/debug.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/decision/ledger.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/decision/records.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/decision/replay.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/distributed/__init__.py` | 存疑 | 仅 pytest v3 distributed fabric 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/distributed/coordinator.py` | 存疑 | 仅 pytest v3 distributed fabric 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/distributed/membership.py` | 存疑 | 仅 pytest v3 distributed fabric 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/distributed/transport.py` | 存疑 | 仅 pytest v3 distributed fabric 与架构文档可达，尚未接入当前 server 生产路径。
`src/ombrebrain/domain/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/domain/boundary.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/domain/commands.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/domain/invariants.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/eventsourcing/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/eventsourcing/contracts.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/eventsourcing/kernel.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/fabric/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/fabric/log/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/fabric/log/snapshot.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/fabric/log/wal.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/fabric/storage/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/fabric/storage/engine.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/kernel/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/kernel/context.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/kernel/errors.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/kernel/registry.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/maintenance/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/maintenance/code_fingerprint.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/maintenance/migration_contract.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/maintenance/report.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/maintenance/vnext_coverage.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/microkernel/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/microkernel/contracts.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/microkernel/runtime.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/observability/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/observability/metrics.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/plugins/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/plugins/contracts.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/plugins/runtime.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/contracts.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/engine.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/formal_invariants.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/red_lines.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/static_surfaces.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/surfacing.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/update_policy.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/policy/vm.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/projection/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/projection/audit_runtime.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/projection/auditor.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/projection/journal.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/projection/observation.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/projection/observers.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/projection/runtime.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/protocol/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/protocol/manifests.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/protocol/public_tools.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/protocol/schemas.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/resilience/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/resilience/recovery.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/resilience/scanner.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/retrieval/__init__.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/retrieval/context.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/retrieval/engine.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/retrieval/planner.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/retrieval/scoring.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/ombrebrain/version.py` | 活 | 从 server v3 runtime、生产诊断/策略/热更新链静态可达。
`src/projection_mirror.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/projection_sqlite.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/projection_vector.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/provider_detect.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/reclassify_api.py` | 活 | 独立维护 CLI，带 __main__ 且有文档/测试引用。
`src/retrieval_eval.py` | 活 | 由 tools/evaluate_retrieval.py 与测试引用的检索评测库。
`src/server_app.py` | 活 | 生产 HTTP/ASGI 中间件与生命周期装配，由 server.py 启动路径调用。
`src/server.py` | 活 | Docker、Render、裸机共同生产入口；装配 14 个 MCP 工具与全部 Web 路由。
`src/tools/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/_common.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/_runtime.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/anchor/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/anchor/core.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/breath/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/breath/_verbatim.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/breath/catalog.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/breath/feel.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/breath/importance.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/breath/search.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/breath/surface.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/dream/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/dream/candidates.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/dream/hints.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/dream/output.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/grow/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/grow/core.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/grow/shortpath.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/hold/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/hold/core.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/hold/feel.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/hold/pinned.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/i/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/i/core.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/plan/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/plan/core.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/trace/__init__.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/tools/trace/core.py` | 活 | 经 server.py 的 14 个 FastMCP 注册薄封装传递可达。
`src/utils.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/vault_health.py` | 活 | 从 server.py 生产入口直接或传递可达。
`src/VERSION` | 活 | 运行、镜像播种与 Dashboard 热更新共同读取的版本契约。
`src/web/__init__.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/_shared.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/auth.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/buckets.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/config_api.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/dashboard.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/embedding.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/github.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/hooks.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/import_api.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/letters.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/meta.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/oauth.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/ollama_local.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/onboarding.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/plans.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/request_limits.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/search.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/system.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/tunnel.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/web/v3_debug.py` | 活 | 经 web.register_all、共享运行时或 server_app 的生产路由链可达。
`src/write_memory.py` | 活 | 独立维护 CLI，带 __main__ 且有文档/测试引用。
`tests/__init__.py` | 活 | 测试包边界，支持 tests.dataset 等包导入。
`tests/conftest.py` | 活 | pytest 自动加载的 fixture/环境装配。
`tests/dataset.py` | 活 | 由 tests/test_scoring.py 导入的固定回归数据集。
`tests/mcp_llm_stub.py` | 活 | Docker MCP 集成测试使用的确定性 OpenAI-compatible stub。
`tests/test_adr_requirements_phase20.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_api_timeout_config.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_archive_collision.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_atomic_config_yaml.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_atomic_write.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_auth_input_validation.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_backup_archive.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_backup_import_safety.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_bm25_async_rebuild.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_breath_catalog.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_breath_mcp_compat_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_breath_query_catalog_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_breath_surface_zero_emotion_tiebreak.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_breath_verbatim_patch.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_bucket_concurrency_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_bucket_type_migration_contract.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_code_fingerprint.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_code_health_regressions.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_code_standards_phase17.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_command_boundary_phase18.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_comprehensive.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_context_serialization_phase8b.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_crash_recovery_phase13.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_bucket_edit_persistence.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_bucket_view_state.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_diagnostics_panel.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_env_config_contract.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_github_config_contract.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_import_preflight.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_memory_editor_contract.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dashboard_update_source.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_data_dir_persistence.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_datetime_metadata_normalization.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_decay_plan_letter_no_autoresolve.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dehydrator_output_icon.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_dehydrator_response_boundary.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_developer_test_data_erasure.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_docker_tunnel_persistence.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_embedding_api_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_embedding_outbox.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_entrypoint_code_bootstrap.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_env_config_identity.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_feel_flow.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_fetch_cloudflared.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_formal_invariants_phase10.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_formal_invariants_phase8a.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_gen_update_manifest.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_github_backup_alarm.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_github_backup_manifest.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_github_config_api.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_github_sync_long_path.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_github_sync_memory_bounds.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_github_sync_zero_commit.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_grow_items.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_hot_update_persistence.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_import_extraction_json.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_import_memory_regressions.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_import_preflight.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_ledger_mirror_phase1.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_ledger_property_phase5b.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_ledger_replay_phase5a.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_letter_author_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_letter_dashboard_regressions.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_letter_read_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_list_all_cache.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_llm_quality.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_login_rate_limit.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_maintenance_tool_safety.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_mcp_open_access_warning.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_mcp_static_token_auth.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_mcp_tools_docker_integration.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_media_store.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_memory_boundary_regressions.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_migration_contract_phase15.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_migration_engine_atomic_swap.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_multi_owner_isolation.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_multi_owner_launcher.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_neural_tool_router_phase8c.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_oauth_refresh_token.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_observability_boundary_phase12.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_owner_identity.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_password_kdf.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_permanent_breath_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_pinned_quota_web_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_pinned_visibility_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_plugin_agency_boundary_phase11.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_priority4_confusion_cleanup.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_projection_mirror_phase2.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_public_tool_design_phase16.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_quota_counter_sync_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_quota_race_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_reclassify_api.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_red_lines_phase21.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_red_team_regressions.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_release_audit_regressions.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_render_blueprint_contract.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_render_config_path.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_replication_contract_phase14.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_restart_api.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_retrieval_eval.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_retrieval_resilience.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_retrieval_scoring_phase9.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_rust_kernel_phase6a.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_scoring.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_search_similar_vectorized.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_secure_onboarding.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_security_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_server_app.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_server_proxy_header_contract.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_sqlite_projection_phase2b.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_surface_context_compiler_phase19.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_surface_policy_phase3.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_system_diagnostics.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_tombstone_erasure_phase4.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_tool_output_contract_phase8d.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_touch_hotpath.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_trace_importance_regression.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_tunnel_autostart.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_update_compile_guard.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_update_integrity.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_update_source_gate.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_architecture_audit.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_architecture_docs.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_bucket_adapter.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_capability_catalog.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_capability_microkernel.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_collab_graph.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_consensus.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_consistency_auditor.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_dashboard_debug_view.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_debug_web_api.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_decision_debug_service.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_decision_record.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_decision_replay.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_distributed_fabric.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_event_sourced_kernel.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_formal_acceptance_harness.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_kernel_registry.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_bucket_integration.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_command_bridge.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_component_attachment.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_execution_pipeline.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_module_profiles.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_runtime.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_server_wiring.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_tool_entrypoints.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_tools_runtime.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_legacy_web_integration.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_maintenance_report.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_memory_command_router.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_memory_event.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_memory_fabric.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_memory_invariants.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_migration.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_package.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_plugin_runtime.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_policy_contracts.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_policy_engine.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_policy_vm.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_projection_observers.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_projection_runtime.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_query_planner.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_raft_cluster.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_release_acceptance.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_release_docs.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_resilience_scanner.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_snapshot_catchup.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_static_surfaces.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_update_policy.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_v3_wal.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_vault_health.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_vector_projection_phase2c.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_version_consistency.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_vnext_preflight_report_phase22.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tests/test_web_api_docker_integration.py` | 活 | pytest 可收集测试文件；本次 collect-only 已确认进入 1288 项测试集合。
`tools/backfill_embeddings.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/check_buckets.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/check_icloud_conflicts.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/clean_orphan_embeddings.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/debug_decision.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/diagnose_permanent_reads.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/evaluate_retrieval.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/fix_unpinned_permanent.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/migrate_feel_domain.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/reclassify_domains.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/v3_health_report.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`tools/vnext_preflight.py` | 活 | 有 __main__ 的维护/诊断 CLI，并有文档、测试或调用方引用。
`VERSION` | 活 | 运行、镜像播种与 Dashboard 热更新共同读取的版本契约。
`zbpack.json` | 活 | 生产构建、启动或平台部署入口。

### 第一阶段结论

当前没有高置信死 Python **文件**；明确死文件 2 个，明确死/冗余符号若干，另有 13 个只在 vNext 预研测试/文档中存活的模块和 1 个手工 Compose overlay。第二阶段可以安全清理私有死代码、孤儿资产和失效依赖文件；公共协议、兼容槽与预研模块暂不删除。

## 第二阶段：代码质量、安全与架构扫描

### 扫描基线

| 检查 | 结果 | 说明 |
|---|---:|---|
| Ruff 0.15.21 | 1 → 0 | 唯一默认规则问题为 `src/web/buckets.py` 未使用 `os`，已清理。 |
| Ruff 扩展探查 | 619 个候选 | `BLE001` 389、`C901` 90、async 阻塞调用 32、性能类 35、未持有 `create_task` 16；多数需按语义治理，不能机械批量改。 |
| Bandit | 高危 0、中危 0 | `-ll -ii`；仅有旧 `nosec` 注释未对应当前告警的提示。 |
| pip-audit | 0 个已知漏洞 | 基于带 hash 的 `requirements.lock.txt`。 |
| Radon CC | 1,691 blocks | F 11、E 4、D 20；前 134 个复杂块均值 D（21.15）。 |
| Radon MI | 3 个 C | `bucket_manager.py`、`web/system.py`、`ombrebrain/maintenance/report.py`。 |
| Python compileall | 通过 | `src/ tools/ deploy/` 全量语法编译通过。 |

### 已在本阶段修复

1. **SSE 鉴权绕过（Critical）**：原中间件只匹配 `/mcp`，legacy SSE 的 `/sse` 和 `/messages/` 可在 `mcp_require_auth=true` 时无 Bearer 通行。新增传输感知 matcher，鉴权、body limit、Accept shim 和 CSRF 豁免统一覆盖 SSE 两条路径，OAuth 仍绑定同一规范 `/mcp` resource。
2. **首启管理员抢占/并发双会话（High）**：`/auth/setup` 增加进程级 async lock 和锁内二次检查；远程首启默认拒绝，无显式 `OMBRE_SETUP_TOKEN` 时同时要求 socket peer 与唯一 `Host` 均为明确回环地址，阻断 DNS rebinding。Render Blueprint 自动生成 Dashboard 密码；用户/VPS/多人 Compose 强制非空密码且默认只绑 `127.0.0.1`。
3. **存储型 XSS 与 YAML alias bomb（High/Medium）**：被篡改的 frontmatter 可把 `importance` / `activation_count` 字符串直接注入 Dashboard `innerHTML`。现在读边界统一数值化/限幅，前端再次 `Number.isFinite` 防御。metadata normalization 同时限制 16 层/10,000 节点并拒绝重复容器，防 PyYAML 递归/指数别名耗尽 CPU/RAM。
4. **容器入口可递归删除记忆卷（High）**：`entrypoint.sh` 原会对可配置 `OMBRE_CONFIG_PATH` 执行 `rm -rf` / `find -delete`。现在只要目标是目录就 fail closed，绝不自动删除。
5. **GitHub 备份/恢复边界（Medium）**：上传不再跟随 `.md` symlink；恢复拒绝 truncated tree、超过 10,000 文件/5 MiB 单文件/512 MiB 总量/超长或重复路径，拒绝 symlink/junction 父路径。有 manifest 时强校验 schema、文件集、size 和 SHA-256，错误不再回 `ok:true`。sync/import 共用锁，Web 恢复事务串行，预备份名增加 ns+UUID。
6. **multipart 磁盘 DoS（Medium）**：历史导入和 ZIP 迁移原先 `request.form()` 完整 spool 后才检查文件大小。现在包装 ASGI receive，对 Content-Length 和 chunked 实际字节都做总请求上限，同时限制 multipart fields/files。
7. **密钥进 URL/日志（Medium）**：Gemini 原生 API 不再使用 `?key=`，统一改为 `x-goog-api-key`，避免 httpx 异常把 key 写入日志/E001/API 响应。Webhook 日志不再回显带签名 path/query 的 URL 或 URL-bearing exception。
8. **OAuth 撤销和浏览器边界（Medium）**：初始设密、改密码、安全问题恢复现在同时撤销 access/refresh/code；refresh token 每次使用都旋转。统一响应头增加 `frame-ancestors 'none'`、`DENY`、`nosniff`、`no-referrer` 和 Permissions-Policy，防 OAuth 授权页点击劫持。
9. **供应链可重现性（High/Medium）**：Lucide 由 `latest` 改为 `1.24.0` + SHA-384 SRI；cloudflared 固定 `2026.7.1` 且按四架构校验官方 SHA-256；Ollama 固定 `v0.32.0`，按 OS/架构校验官方 SHA-256，限制下载、成员数、单成员、总展开量和压缩比，且复核重定向终点 host。Render 改用带 hash lockfile。
10. **Tunnel 凭据（Medium）**：`.tunnel_config.json` 改用 0600 原子私密写；token 通过子进程环境传入，不再出现在 `ps` / `/proc/*/cmdline`。
11. **质量/交付清理**：删除失效 `requirements-local.txt`、私有死函数/常量/计数器/前端 wrapper/废弃 wikilink 状态；审阅 API 空决策正确计错，前端不再在服务端失败后佯装成功。`.dockerignore` 排除 coverage、测试 vault、Rust target/整个 kernel、tools 和 CI 资产；pytest 全局 vault 改用进程临时目录，不再在仓库留 `test_buckets/`。

### 尚未完成的风险与优先级

| 等级 | 位置 | 问题 | 建议/后续验证 |
|---|---|---|---|
| 高（数据完整性） | `web/buckets.py::rename_human_in_buckets` | 直接遍历私有目录并 `open(...,"w")`，绕过 BucketManager 锁、原子写、ledger/projection/outbox；并发更新可丢写，中断可截断文件。 | 第四阶段先做并发特征测试，再迁入 BucketManager 受锁事务。 |
| 高（发布阻断） | `LICENSE`、README、noncommercial notice | MIT 明确允许商用，README/附加声明又声称非商用，且 notice 版本仍停在 2.4.0。 | 需权利人/法律决策；工程审计不自主改变授权条款。 |
| 高/中（可用性） | `web/meta.py` 热更新 SSE | async handler 内同步 `copytree/rmtree/ZIP/subprocess.run(pip, timeout=600)`，可冻结全部 MCP/Web。 | 整条安装/回滚流水线移至 worker process/thread，用队列返进度。 |
| 中高（OOM） | `backup_archive.py`、`/api/export` | 先将全部 Markdown、SQLite、ZIP BytesIO 及 `getvalue()` 同时留在内存，所谓 StreamingResponse 只是一次发整个 bytes。 | 第三/四阶段用大 vault 测 RSS；改为临时文件 ZIP + FileResponse 和导出锁。 |
| 中（并发） | `MigrateEngine.parse_zip` / `/api/migrate/upload` | `is_busy` 不含 parsing；两个 ZIP 可交错覆盖共享 `_parsed_buckets/_conflicts/...`，apply 可导错包。 | 增加 parsing phase + lock + generation ID，apply 必须匹配该 ID。 |
| 中（并发/误报） | 历史导入 upload/start | 路由检查 `is_running` 与后台任务真正设置 `_running` 之间有竞态；两个并发请求都可能返回“已启动”，第二个任务随后被静默忽略，且上传内容的生命周期互相重叠。 | 增加原子 reserve/job ID；只有成功占位的请求返回 started，失败请求返回 409。 |
| 中（可用性） | `BucketManager.get_stats` / `/health` | 每次同步 O(N) `walk/stat` 全 vault，健康探针在大库上可阻塞事件循环。 | 缓存计数/后台盘点，至少 `asyncio.to_thread`。 |
| 中（长期 OOM/磁盘） | `errors.py::recent_errors`、`web/system.py::/api/logs` | 限返回条数但先 `readlines()` 整个无轮转 JSONL/日志文件。 | 倒序分块/deque 读尾 + 大小轮转和单条上限。 |
| 中（OAuth DoS） | `/oauth/register` | 公开 DCR 可持久填满 1,024 个、TTL 365 天，容量满后不驱逐；这次已修 grant 撤销/旋转，但 DCR 滥用边界仍在。 | IP+全局限速、短未使用 TTL、容量满驱逐最旧未用项。 |
| 中高（认证 DoS） | `/auth/login`、`/auth/recover` | PBKDF2(240k) 在 async 路由同步执行，本机单次错误口令约 66 ms；约 15 req/s 可长期占用事件循环。现有限流仅按来源 IP，状态字典也无全局 TTL/LRU 上限。 | 第四阶段验证事件循环饥饿；增加全局 token bucket、带并发上限的 worker、IPv6 /64 归一化和有界 TTL/LRU。 |
| 中（持久间接 Prompt 注入） | `tools/dream/output.py` | `dream` 将可写入/导入的桶正文与“可调用 trace/hold”的建议拼在同一文本层；恶意记忆可能被下游模型误当指令，造成跨会话行为劫持或记忆篡改（不是服务器 RCE）。 | 第四阶段加入持久化注入用例；输出增加可信来源与 data boundary，复用 imperative 标记/中和，并评估 OAuth 读写 scope 与高风险 mutation 确认。 |
| 中（凭据周期） | Dashboard sessions | 仅轮换 `OMBRE_DASHBOARD_PASSWORD` 并重启不会撤销已持久 30 天 session。 | session 存 auth epoch/凭据 fingerprint，变更即 revoke-all。 |
| 中（供应链） | 热更新、CI/Docker | 根目录无生产 `update_manifest.json`，无清单仍继续；默认取可变 `main`。Actions/base image/Compose images 仍为移动 tag，workflow 未显式最小 `permissions`，镜像无签名/attestation。 | 发版生成并强制 manifest，固定 tag/commit/digest，Actions pin SHA，加 provenance/SBOM/signature。 |
| 中（隐私） | Dashboard | 仍自动请求 Google Fonts，并按 timezone 推导城市后请求 Open-Meteo；本次已加 no-referrer，但 IP/近似城市仍会出站。 | 自托管字体，天气改为明确 opt-in，文档列所有出站连接。 |
| 中/低 | CORS、hook、公开健康/引导信息 | CORS `*` 仍覆盖整个 app（CSRF guard 已防 unsafe cookie 请求）；`/breath-hook?token=` 会把 secret 放入日志/历史；`/health` 公开 bucket/decay，异常原样返回路径类 detail；Dashboard 缺文件页回绝对路径，公开 onboarding status 暴露配置来源与能力状态。 | CORS 只作用 bearer MCP；hook 只接受 header；public health 只返固定 status/error code；缺文件不回路径；引导状态只保留 UI 必需布尔值并 `no-store`。 |

### 复杂度与架构建议

- 最高复杂度：`web/system.py::build_system_diagnostics` F156，`tools/trace/core.py::trace_core` F119，`tools/breath/surface.py::surface_default` F94，`bucket_manager.py::_update_locked` F88，`create` F63，`surface_search` F51。当前 2.7.1 bugfix 正好集中在 breath/trace/bucket 边界，不应在无更强特征测试时整体重写。
- `server.py` import-time 构造 + `tools._runtime` / `web._shared` 全局注入使测试隔离和多实例并行困难。建议逐步用显式 `RuntimeContext` + app factory 取代。
- 16 处未持有 `asyncio.create_task`、389 处宽泛异常和至少 52 处静默 `pass/continue`。建议引入统一 task supervisor（持有、记录异常、shutdown cancel/await），并按“用户错误/数据损坏/外部服务降级”分类处理，不机械替换所有 `except Exception`。
- 重复边界：tool/web runtime envelope、breath/Web semantic scoring、payload sanitizer、hold normalization、lock-file 协议均各有两份实现。建议先抽纯函数/协议，不直接合并有副作用的 handler。
- Dashboard 仍是约 9k 行单 HTML/CSS/JS，`web/__init__.py` eager import 18 个路由并依赖 `_shared` 全局。前端先拆 transport/import/diagnostics ES modules；Web 先引入 route manifest + 显式 context。

### 第二阶段静态验证

- `python -m compileall -q src tools deploy`：通过。
- `ruff check src tools deploy tests --no-cache`：通过（0 项）。
- `bandit -r src tools deploy -ll -ii -q`：通过（高/中 0）。
- `pip-audit -r requirements.lock.txt --progress-spinner off`：无已知漏洞。
- `git diff --check`：通过。
- 本阶段按顺序要求未运行 pytest；所有动态回归、覆盖率、Docker 实例及恶意输入将在第三/四阶段执行。

### 第二阶段结论

当前普通 lint 和已知依赖 CVE 不是主要风险；主要风险集中在 async 主循环中的同步大 I/O/子进程、绕过统一存储事务的直写、大数据导出/日志内存峰值，以及发布供应链/许可证一致性。本阶段已关闭可直接证明的 Critical/High 鉴权、XSS、删数据与可执行下载完整性问题；剩余大重构项先进入第三阶段建立动态基线。

## 第三阶段：测试与覆盖率

### 本地 pytest 与覆盖率

| 项目 | 结果 |
|---|---:|
| 收集测试 | 1,387 |
| 通过 | 1,309 |
| 跳过 | 78 |
| 失败 | 0 |
| warnings | 2 |
| 语句覆盖率 | 70.94%（20,495 statements，5,956 missed） |
| CI 门槛 | 60%，已通过 |
| 耗时 | 79.20 s（Windows / Python 3.10.5） |

命令与 CI 一致：`pytest tests -q --asyncio-mode=auto --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=60`。两条 warning 均来自测试故意生成重复 ZIP 成员来验证更新包拒绝逻辑，不是运行时异常。跳过项主要为未配置外部 LLM key、POSIX-only 行为、Windows symlink 权限，以及未设置 Docker URL 时的 Docker-only 用例；这些 Docker 用例随后在隔离容器中单独执行。

覆盖率低点仍需后续增量治理：`tools/breath/feel.py` 11%、`tools/dream/hints.py` 15%、`tools/anchor/core.py` 18%、`web/buckets.py` / `web/letters.py` 21%、`web/embedding.py` 23%、`web/hooks.py` 26%、`web/search.py` 32%、`web/ollama_local.py` 36%。这些模块不宜靠无断言的行覆盖“刷数”，应优先覆盖写入回滚、外部失败和并发状态机。

### 14 个 MCP 工具 Docker 集成矩阵

反馈中的“12 个工具”是旧口径；当前 `server.py` 实际公开 14 个，测试严格断言无缺失、无额外暴露。使用当前工作树派生镜像、一次性 named volume、`mcp_require_auth=false` 的隔离测试端口执行，共 **64 passed / 0 failed（3.87 s）**。

| 工具 | 已验证契约 |
|---|---|
| `breath` | 公共 0 参数 schema、无参浮现、旧 9 参数缓存客户端兼容、未知参数拒绝。 |
| `breath_search` | 必填 query、精准回传原文、结果数与 query 长度边界。 |
| `breath_advanced` | query 命中优先、`max_results` 最终生效、catalog 仅元数据、类型异常。 |
| `hold` | 创建/返回 bucket ID、feel/source 约束、test_data 约束、超大桶拒绝、并发同内容收敛。 |
| `grow` | `items` 成功写入、无 provider 的长文降级、源文本/条目数上限、错误不残留桶。 |
| `trace` | 元数据更新、no-op、长原文保全、路径穿越形状 ID、超大替换不丢原文、并发更新不损坏。 |
| `anchor` | 必填 ID、钉选成功与重复调用幂等。 |
| `release` | 必填 ID、取消钉选成功与重复调用幂等。 |
| `pulse` | 系统摘要、`include_archive` 对归档显示的控制、类型异常。 |
| `plan` | 创建、状态过滤/非法状态回退、相关桶与重复语义。 |
| `letter_write` | 必填 author/content、正文逐字保存、自定义署名。 |
| `letter_read` | query/author/date/limit 过滤、自定义作者读取、类型异常。 |
| `I` | self 描述写入/读取、aspect/read/limit 边界。 |
| `dream` | 最近完整记忆、`window_hours` 上下界钳制、类型异常。 |

集成测试还统一覆盖 14 个工具各自的 schema-invalid 请求，确保 MCP 返回结构化 `isError`，而不是连接中断或裸异常；HTTP 层另验证全局超大 body 返回 413。测试容器和 volume 已删除，未挂载仓库 `buckets/` 或真实用户数据。

完整 Dockerfile 的联网重建在 PyPI 下载 `annotated-types==0.7.0` 时遭遇环境侧 `SSL: UNEXPECTED_EOF_WHILE_READING`，cloudflared 上游请求也同样不稳定；这不是代码/摘要失败。为区分网络与产品问题，真机测试改用本机已有且相同锁依赖的镜像层，覆盖当前完整 `src/frontend/entrypoint/config/docs` 后离线派生。另用全新 volume 跑 Dashboard 管理 API 流程：**1 passed**，覆盖远程 setup 无 token 403、显式 bootstrap token、认证会话、配置读写、恶意 JSON、chunked 超限和退出登录。CI 已同步加入测试 setup token。

### 新增边界/异常回归与测试中修复

- 新增 99 个 pytest node；重点包括 SSE `/sse`/`/messages` 全路径鉴权、Security Headers、并发首启单会话、Gemini key 不进 URL、Webhook 不泄露签名 URL、multipart chunked 上限、下载摘要/大小、GitHub manifest/traversal/symlink、OAuth refresh 单次轮换与重放拒绝。
- 首轮 126 项回归虽然全过，但 Windows 退出时发现 `Dehydrator` 持久 SQLite cache 句柄未关闭。新增幂等 `close()` + finalizer；文件现在可立即删除，退出清理不再报 WinError 32。
- metadata alias 限制原先按每个顶层字段重置 budget，跨字段共享 alias 仍可放大。改为对整个 metadata graph 一次归一化，递归、共享 alias、20 层深度和恶意数值均有负例。
- GitHub restore 在限额检查前读取 manifest blob；现在先验证 tree 声明 size，再限制 base64/decoded 大小并严格解码。cloudflared 下载新增 Content-Length 与实际流 128 MiB 双上限，失败保留旧目标且删除 `.part`。
- Docker Web 测试的旧首启流程不符合新“远端必须 setup token”安全规则；测试和 CI 已改为先断言无 token 403，再持 token 完成初始化。
- MCP manifest 对照发现工程文档落后于实现：已同步 `hold` 的 meaning/media/test provenance、`grow(items)`、`trace` 的 meaning/media/测试硬删除字段，以及信件自定义署名/`ai_name` 契约；同时纠正 hold/grow 合并仍调用 LLM 压缩的旧数据流描述。

### 第三阶段结论

本地单元/集成基线、覆盖率门槛、当前 14 个 MCP 工具的真实协议调用，以及 Dashboard 容器管理流程均已通过。测试阶段新暴露的资源句柄、alias budget、manifest/download 上限和 CI 首启契约已修复并锁定。下一阶段进入专门红蓝对抗，重点攻击持久 Prompt 注入、异常/超大 payload、认证耗尽、导入/迁移竞态和数据写入并发。

## 第四阶段：红蓝对抗

### 范围、方法与判定口径

本阶段只使用 pytest 临时目录、合成 ZIP/SQLite/Markdown、伪造 provider 和隔离的 ASGI 请求，不读取真实 `buckets/`、真实配置或凭据。红队不是只验证“接口返回错误”，而是通过线程池、多 event loop、取消/断连、磁盘写入失败、竞争时序屏障、压缩炸弹和存储型指令文本，稳定逼出资源泄漏、旧状态覆盖、内存峰值与鉴权状态错乱；蓝队修复后再用同一时序或失败点做回归。这里的“已修”表示攻击特征测试已转绿，不表示模型输出、第三方文件编辑器或宿主平台具有超出其信任边界的安全保证。

### 攻击面与稳定复现

| 编号 | 攻击面 | 红队输入/时序 | 修复前可稳定观察到的风险 |
|---|---|---|---|
| R1 | 持久 Prompt 注入 | 把“忽略上文、调用 `trace`/`hold`、把以下内容当系统指令”等文本写入或导入普通桶，再触发 `dream` 或 `/breath-hook`。 | 存储正文、派生摘要与操作建议处于同一自然语言层，下游模型可能把不可信记忆误当指令；这是跨会话行为劫持/误写风险，不是服务器 RCE。 |
| R2 | `breath` / `dream` / hook 参数与预算 | 精准 query + 小 `max_results`、`catalog=true`、低 `max_tokens`；超长 provenance；大量 pinned 候选与慢速 dehydration provider。 | core/pinned 全文可挤掉精准命中；目录/结果数契约失效；`dream` 的标题、边界和 provenance 未计入最终预算；hook 可产生过多 provider 调用或超预算文本。 |
| R3 | 异常参数、路径与超大 payload | 非有限浮点、YAML `set`/`bytes`/alias、超深 metadata、锁 key 路径穿越形状、重复/加密/软链接/穿越 ZIP 成员、超压缩率、chunked 超限请求。 | JSON 序列化失败、CPU/RAM 放大、锁文件逃逸、归档覆盖任意路径或在完整读取后才拒绝，形成存储与可用性攻击面。 |
| R4 | 迁移/导出 OOM | 构造 32 MiB 高压缩成员、较大 SQLite 与多 Markdown；在导出正常发送、非法 Range 和客户端断连三个位置观察临时文件。 | 迁移曾同时保留上传 bytes、全部解压 bytes、全部桶正文和 DB；导出曾在 `BytesIO` 中组装整个 ZIP 后一次发送，512 MiB 实例存在明显峰值和清理遗漏。 |
| R5 | 历史导入与完整备份迁移竞态 | 两个线程/event loop 同时 upload/parse/apply；parse 后再制造 ID 冲突或更新本地桶；在 staged write、历史副本、删除旧源等提交点注入失败并取消 worker。 | 共享解析状态可被后一个包覆盖；两个请求都可能声称启动成功；`overwrite` 的删旧再写新可丢记忆；取消 `to_thread` 后过早释放槽位会与仍运行的 worker 竞争。 |
| R6 | bucket 锁、缓存与外部写入 | 六个独立 event loop 竞争同一桶；把活锁文件 mtime 改旧；create/migrate 同 ID；ripple 与 touch/archive 交错；硬删时改变 provenance；缓存构建中并发失效。 | `asyncio.Lock` 跨 loop 失效、按年龄偷走仍存活 lease、lost update/复活归档桶、测试数据保护检查 TOCTOU，以及旧缓存覆盖新磁盘内容；逐次找 ID 还会退化为 O(N²) frontmatter 扫描。 |
| R7 | Dashboard auth 资源耗尽与状态原子性 | 并发错误口令/恢复请求、IPv6 来源变化、两个旧密码同时换密、落盘失败、session 保存失败。 | PBKDF2 可阻塞事件循环；仅来源限流可被摊薄且状态无界；并发换密可能双赢；持久化失败时内存凭据/session 与磁盘事实不一致。 |
| R8 | OAuth DCR、code、refresh 与 revoke | 高频匿名注册；并发兑换同一 code/refresh；换密/revoke 与正在签发 code 交错；模拟 token 状态落盘失败。 | DCR 可填满长期容量；授权码或 refresh 可能被重复消费；撤销与签发竞争可复活旧 grant；失败路径可能“返回成功但未持久化”。 |
| R9 | 热更新 | 从另一线程/event loop 发起第二个更新；ZIP 检查或源文件写入中断开 SSE；在阻塞检查、备份、apply、compile/pip 阶段探测事件循环。 | loop-local 状态不能防双更新；同步文件树/ZIP/子进程冻结 MCP/Web；断连后 worker 仍在跑却提前解锁，或新版本只写了一半且临时目录残留。 |
| R10 | embedding 后端迁移与 Ollama pull | 两个迁移/拉取请求同时进入；准备 staging、provider 调用或 outbox 清理时取消/失败；更换 backend/model/dim 后继续旧 checkpoint。 | 检查与占位分离导致双任务；旧实现原地混写 `embeddings.db`，失败可留下新旧维度混合库；旧 checkpoint 可能被错误续用。 |
| R11 | GitHub 配置、备份与恢复 | 并发保存不同 config key、原子写失败、深层 Windows 路径、symlink Markdown、超大/truncated tree、恶意 manifest/hash、超大 tree 请求体。 | UI 可报保存成功但重启后配置消失；备份会跟随链接或在内存构造无界请求；恢复可在缺页、路径或哈希不一致时写入不可信数据。 |

### 蓝队修复

1. **不可信文本分层（R1/R2）**：`dream` 与 breath hook 把 STORED/DERIVED 内容包装为带来源、SHA-256、字符数、`instructions:false`、`may_call_tools:false` 的显式数据块，不再把正文和工具建议混成一层。超长 provenance 只保留有界摘要和 digest。`breath` 的 query、`max_results`、`catalog` 和最终 token 预算在 surface/render 末端统一约束：精准命中优先，catalog 只出每桶一行元数据，core/pinned 不再无条件全文前置。
2. **最终输出与 provider 成本都设硬边界（R2）**：`dream` 按“最新完整 → 可容纳时折叠 → 否则省略”装箱，标题、边界和哈希也计入 `feel_max_tokens`，最终文本有硬上限。hook 默认最多 8 次、硬上限 32 次 dehydration，同时设置单次/总超时、最多 2 个并发 provider、来源+全局限流和有界来源 LRU；跨站 ambient-session GET 被拒绝，token 只从 header/Bearer 读取，响应 `no-store`，webhook 遥测也有超时。
3. **入口先拒绝、归档边读边验（R3）**：HTTP body/multipart 同时校验声明长度和实际 chunk；metadata 统一限深、限节点、限字节，拒绝循环/共享 alias、集合、bytes 与非有限数。ZIP 在落盘解压前拒绝重复、加密、symlink、路径穿越、成员数/单项/总量/压缩比越界，流式读取中再次执行字节上限；bucket lock key 先 SHA-256，再进入固定 `.locks` 目录。
4. **迁移、导出改为磁盘背书（R4）**：迁移在读取 request body 前先占 parse 槽，上传流入私有 spool 文件；归档成员按 1 MiB 块解到私有平面 workspace，生产 `_ParsedBucket` 只留路径，SQLite 也按路径校验/合并，apply/reindex 一次只读一个桶。默认单桶正文 50 KiB、metadata 16 KiB，并保留可配置但仍有限的安全顶。导出先做 SQLite 页数×页大小预检，再写临时 ZIP，压缩输出过程中持续检查上限并以可清理 `FileResponse` 发送；正常、Range 提前返回和断连均进入 `finally`。历史导入在完成/失败后释放原始 chunks。
5. **状态机预占、代际绑定与事务提交（R5）**：完整备份迁移使用跨 thread/loop 的状态锁和不可伪造 generation；parse/upload/apply 都先 reserve，apply 只能消费匹配 generation 一次。取消时 shield/reap 后台线程，再清 workspace 和释放槽位。apply 在 BucketManager 的同一 bucket turn 内重新检查冲突；`overwrite` 先写完整 staged 新桶和唯一历史副本，再提交，旧源删除失败会回滚目标/历史。历史对话导入同样用原子 reserve/job ID，失败请求明确 409，不再静默丢任务。
6. **统一存储 turn 与缓存 CAS（R6）**：bucket turn 使用散列命名的 OS 内核文件 lease，活 lease 不按 mtime 被偷走，进程崩溃由内核自动释放。create 在同一 turn 内最终分配 ID，并以临时文件 + no-overwrite hardlink 提交；migration/create 因而不能互相覆盖。ripple 释放 source 后逐个锁 target 并重读，hard delete 在锁内重验 provenance，human rename 迁入 BucketManager 全局事务。活跃桶缓存改用跨 loop 线程互斥、文件指纹和 managed-write generation CAS；外部内容变更会刷新缓存并进入 embedding outbox，删除会清派生索引；批量 ID index 消除反复 frontmatter 全扫。
7. **认证耗尽与凭据切换原子化（R7）**：PBKDF2 放入带并发上限的 worker；登录/恢复采用来源和全局双限流、IPv6 `/64` 聚合、有界 TTL/LRU。auth JSON 更新使用跨线程锁和 generation/CAS；旧密码并发旋转只能一个成功。新 session 候选先持久化再发布，失败返回 503；密码、安全问题和 session 变更不再留下“内存成功、磁盘失败”的半状态。
8. **OAuth grant 全生命周期串行化（R8）**：DCR 采用每来源 10/min、全局 120/min，来源表最多 2,048 项；未激活 client 1 小时过期，容量只驱逐最旧未激活项，不驱逐已使用 client。code、refresh rotation、revoke 由同一跨线程锁和 compare-and-swap 提交；grant generation 使换密/撤销后的在途 authorization 无法回写。token 状态必须先成功持久化才消费旧 grant 或宣称成功，失败时回滚。
9. **热更新单飞、异步卸载与断连回滚（R9）**：在创建 SSE 响应前用进程级 `threading.Lock` 原子占位，跨 event loop 的第二个请求立即 409。下载落盘，ZIP inspect、备份、apply、pip/compile 和清理都移出事件循环；取消会等不可杀的 worker 退出再解锁。源树改动期间断连会先回滚 `VERSION`、`src/VERSION` 和代码/前端，清除临时目录后才释放槽位；成功更新仍可触发重启。
10. **embedding 迁移单所有者（R10）**：迁移、Ollama pull 在第一个 await/读取 body/provider 调用前取得 opaque reservation，失败者 409；只有 owner 能提交/清 outbox。向量迁移实际写 `.migrating` staging DB，完成后原子替换；checkpoint 带 `backend:model:dim` 目标签名，换目标不续用旧进度，取消/失败会释放 owner 并执行清理。
11. **GitHub 持久化与请求内存有界（R11）**：所有 `config.yaml` 更新共用锁、临时文件、`os.replace` 和写后回读；GitHub 配置先落盘，成功后才替换内存实例和后台任务。备份用 `scandir` 惰性遍历，拒绝 symlink，按文件数/单文件/总量限制，tree 分块提交且 manifest 独立受限；恢复串行，拒绝 truncated tree、异常父路径与不一致的文件集/size/SHA-256，Windows 深路径使用长路径边界。

### 测试证据

| 领域 | 回归文件 | 已锁定的关键证据 |
|---|---|---|
| Prompt/预算 | `test_dream_prompt_boundary.py`、`test_breath_hook_security.py`、`test_breath_query_catalog_regression.py`、`test_breath_mcp_compat_regression.py` | 指令形状正文只出现在 data block；provenance 有界；dream 最终 section 不超预算；hook 第 3 个并发 provider 被拒绝；catalog/max_results/query 命中与默认预算契约恢复。 |
| 大包/OOM/清理 | `test_backup_archive.py`、`test_export_streaming_route.py`、`test_import_start_reservation.py` | 32 MiB 解压成员的 tracemalloc Python heap 峰值低于 8 MiB；解析后不保留成员/DB bytes；apply、异常、取消、正常响应、非法 Range 与发送断连都会清 workspace/spool/导出临时文件。 |
| 迁移事务/竞态 | `test_migrate_job_state.py`、`test_backup_archive.py` | 16 个线程争抢 parse 仅一个 owner；stale generation 不能 apply/abandon；parse 后新冲突默认 skip；并发最新编辑成为历史副本；staging、历史写和旧源 unlink 三类失败均保留可恢复的本地记忆。 |
| bucket/cache | `test_bucket_locking_phase4.py`、`test_list_all_cache.py`、`test_human_rename_transaction.py` | 六个独立 event loop 的同 key 临界区最大并发为 1；活 lease 即使 mtime 为 1970 也不被偷走；create/migrate、ripple/archive、hard-delete/provenance 时序无 lost update；24 桶建索引后 200 次 miss 不新增 frontmatter parse；旧 cache builder 不能发布失效快照。 |
| Auth/OAuth | `test_auth_resource_exhaustion.py`、`test_auth_state_atomicity.py`、`test_login_rate_limit.py`、`test_oauth_refresh_token.py` | worker 并发、双层限流与 LRU 有界；旧密码并发换密单赢家；session/OAuth 落盘失败不发布半状态；code/refresh 单次消费；换密/revoke generation 阻止在途 grant 复活；DCR 只驱逐未激活项。 |
| 热更新 | `test_hot_update_concurrency.py`、`test_hot_update_persistence.py`、`test_update_integrity.py` | 跨 loop 双请求单赢家；阻塞阶段运行在线程而主 loop 可继续调度；inspect/apply 中断连会等待 worker、回滚并清临时目录；ASGI 在首次迭代前发送失败也释放 reservation。 |
| embedding | `test_embedding_route_reservations.py` 及 migration 回归 | 双迁移/双 pull 单赢家，loser 在副作用前 409；取消释放 owner；目标签名不符不续传；失败不替换主 DB，成功才原子切换。 |
| GitHub | `test_github_config_api.py`、`test_github_sync_memory_bounds.py`、`test_github_backup_manifest.py`、`test_atomic_config_yaml.py` | 持久化失败不更新内存或回成功；懒扫描与 tree/manifest 请求体都有硬上限；恶意/超大 manifest、hash/file-set 不一致、symlink 与路径越界均在覆盖本地文件前失败。 |

以上是第四阶段专项特征测试的证据，不替换第三阶段已经记录的全量基线，也不把并行修复期间的某次中间态执行数冒充最终交付数字。

### 残余风险与边界

| 等级 | 残余风险 | 当前边界与建议 |
|---|---|---|
| 高（发布/法律） | `LICENSE` 的 MIT 商用许可与 README/noncommercial notice 的“非商用”表述冲突，notice 版本也落后。 | 必须由权利人/法律明确选择并统一文本；本次工程修复未擅自改变授权。 |
| 中（跨进程临时目录） | 正常完成、异常和协作式取消都会清 migration/export/update 临时文件，解析完成但未 apply 也有进程内 TTL sweeper；但进程被 `kill -9`、宿主直接回收或在 workspace 登记前崩溃，仍可能留下孤儿 temp。 | 不能按目录年龄直接删，否则可能删除另一实例的活任务。后续应为 workspace 写入 owner lease（PID + nonce + process birth time/内核锁），只清理确认无活 owner 且超过 TTL 的目录。 |
| 中（外部 writer） | BucketManager 内部写入已共享 OS lease，缓存会轮询发现 Obsidian/脚本的增删改；但外部 writer 不取得该 lease，同一 Markdown 的并发 read-modify-write 和跨多文件事务仍不受 OB 原子性保证。 | 建议外部编辑器使用同目录 temp + atomic replace；若要强一致，需公开 cooperative lock/变更 API 或接入文件 watcher + 冲突版本号，不能只靠 mtime/size。 |
| 中（多 worker 热更新） | 热更新 reservation 是单进程全 event-loop 有效；当前单进程部署满足约束。多个 OS worker 共享同一代码目录时仍可能各自取得锁。 | 多 worker 部署应禁用应用内热更新，或改用跨进程 owner lease/平台发布协调器。 |
| 中（兼容 API 内存） | 生产迁移已经走 `extract_backup_archive_file` 的磁盘路径；兼容用 `read_backup_archive(bytes)` 仍会把归档内容物化在内存。 | 保持私有/测试兼容用途，禁止把它重新接回公开上传热路径；后续可标记 deprecated。 |
| 中（内存结论范围） | 32 MiB 用例证明 Python 解压堆峰值受控；最终 64+1 Docker 集成套件也在严格 512 MiB、无额外 swap 的 cgroup 中通过，采样峰值 155.1 MiB 且 `OOMKilled=false`。但 tracemalloc 与短时 stats 采样不能覆盖所有 OS page cache、SQLite native allocation、第三方 provider、真实大 vault 与并发请求组合。 | 512 MiB 已满足当前隔离集成负载并保有约 356.9 MiB 的观测余量，但不能据此承诺任意生产峰值；生产继续监控 RSS，限制并发，并对更大真实备份做平台侧 soak。 |
| 中（模型信任边界） | data boundary、hash 和 `instructions:false` 显著降低持久注入歧义，但无法数学保证任意下游模型永不遵循数据中的命令。 | mutation 继续依赖服务端鉴权/参数校验；高风险写操作可进一步引入用户确认、scope 分离和策略审计。 |
| 中/低（既有架构/供应链/隐私） | `server.py` import-time 全局运行时、移动的更新分支/部分镜像 tag、无签名发布链、Dashboard 字体/天气出站及全局 CORS 兼容面仍在。 | 按第二阶段建议推进 app factory、固定 digest + SBOM/signature、自托管/opt-in 出站和分路径 CORS；这些不是本轮 bugfix 中可无兼容代价完成的改动。 |

### 第四阶段结论

红队稳定复现的高价值链路已经由蓝队修复并由特征测试锁定：不可信记忆与指令层分离；公开输入、归档和最终输出均有硬预算；迁移/导出不再整包驻留内存；导入、bucket、auth/OAuth、热更新和 embedding 的“先检查后执行”竞态改为原子 reservation/turn/CAS；持久化失败不再伪报成功。仍需 owner 决策或部署级机制处理的事项已明确留在残余风险表中，没有用测试通过掩盖许可证、多进程和外部 writer 边界。

### 最终验证（主线程补录）

- **最终全量 pytest + coverage**：`1444 passed, 78 skipped, 0 failed, 2 warnings in 103.00s`；覆盖率 **74.38%**（22,685 条可执行语句，16,872 covered，5,813 missed），高于 60% 门槛，也高于第三阶段修复前基线 70.94%。
- **最终静态/供应链门禁**：Ruff 0.15.21 通过；Bandit `-ll -ii` 为高危 0、中危 0（仅输出失效 `nosec` 的提示）；`compileall` 通过；`pip-audit -r requirements.lock.txt` 报告 `No known vulnerabilities found`；`git diff --check` 无 whitespace error（仅 Windows 工作树 LF→CRLF 提示）。
- **最终 Docker 协议复验**：用当前最终工作树基于既有同锁依赖镜像，以 `--network=none --pull=false` 离线派生隔离镜像；普通隔离轮的 14 个 MCP 工具矩阵 **64 passed in 3.90s**，Dashboard 管理 API **1 passed in 0.87s**，启动和测试后的 `/health` 均为 `ok`。追加严格 `--memory=512m --memory-swap=512m`（无额外 swap）复验后，MCP **64 passed in 2.99s**、Web **1 passed in 0.83s**；启动 92.79 MiB，测试期间采样最高 154.30 MiB，结束等待 2 秒为本轮最高 155.1 MiB（30.29%），余量约 356.9 MiB；最终状态 `running`、`OOMKilled=false`、`ExitCode=0`。两轮均未挂载真实配置、记忆或密钥。该结果证明当前集成负载适配 512 MiB，不替代更大真实 vault/高并发的 Render 平台 soak。
- **隔离与清理**：最终 Docker 容器、网络、空 volume 和派生镜像均按本轮唯一标签删除，查询计数均为 0；预存容器与基础镜像未触碰。测试生成的 `.coverage` / `coverage.xml` 在提取最终数字后删除。
- **交付状态**：分支为 `main`，`HEAD...origin/main` 为 `0/0`；根目录 `VERSION` 与 `src/VERSION` 均为 **2.7.1**；staged 文件数为 0。整个任务没有创建 commit，也没有 push。
