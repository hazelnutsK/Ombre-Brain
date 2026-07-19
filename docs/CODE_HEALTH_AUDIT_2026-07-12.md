# Ombre Brain 代码健康度审计

审计日期：2026-07-12
审计分支：`testing`
基线提交：`165d60b3da2845aa92553cc2e15733b39f918c4a`

## 第一阶段：代码盘点

### 方法与口径

- 遍历 467 个 Git 跟踪文件；逐文件分析 Python AST import graph、`__main__` 入口、pytest 引用、Docker/工作流/文档引用。
- 生产“活”代码以 `src/server.py` 为根；FastMCP 工具装饰器、`web.register_all()` 动态路由注册、包初始化和静态资源均按真实框架语义处理，不采用 Vulture 的装饰器误报。
- 静态入口可达 148 个 Python 模块；测试/架构路径可达 165 个模块。
- 状态统计：活 360，死 3，存疑 3。文档、许可证和二进制媒体不作为代码判死，未列入下表。
- “活”不等于生产已启用：仅测试验证的 vNext/Rust 脚手架会在说明中明确标出。

### 高置信结论

| 文件/符号 | 状态 | 说明 |
|---|---|---|
| `bm25_index.py` | 死 | 与 `src/bm25_index.py` 完全相同，当前启动、Docker 与测试均使用 `src/` 版本。重复副本存在漂移风险。 |
| `tests.yml` | 死 | 根目录副本不会被 GitHub Actions 执行；与 `.github/workflows/tests.yml` 相同。 |
| `docker-publish.yml` | 死 | 根目录副本不会被 GitHub Actions 执行；与 `.github/workflows/docker-publish.yml` 相同。 |
| `src/web/_shared.py::_verify_password_hash` | 死 | 私有包装函数无调用；实际鉴权直接调用 `_verify_secret`。 |
| `BucketManager.create/update(... allow_embedding_fallback)` | 活 | 参数体内不读取，但注释明确为外部 API 兼容保留，不应按死参数删除。 |
| `src/ombrebrain/kernel/errors.py` 未使用异常类 | 存疑 | 属于 vNext 公共错误分类预留；当前仅 `CapabilityLoadError`、`PolicyViolation` 被运行代码使用。升级契约稳定前不宜直接删。 |

### 逐文件清单

文件路径 | 状态（活/死/存疑） | 说明
---|---|---
`.claude/hooks/session_breath.py` | 活 | 由 .claude/settings.json 的 SessionStart/resume hook 调用。
`.claude/settings.json` | 活 | Claude Code 项目 hook 配置。
`.dockerignore` | 活 | 构建、启动、依赖、版本或平台交付契约。
`.env.example` | 活 | 构建、启动、依赖、版本或平台交付契约。
`.gitattributes` | 活 | 仓库行为配置。
`.github/workflows/docker-publish.yml` | 活 | GitHub Actions 实际工作流入口。
`.github/workflows/tests.yml` | 活 | GitHub Actions 实际工作流入口。
`.gitignore` | 活 | 仓库行为配置。
`Dockerfile` | 活 | 构建、启动、依赖、版本或平台交付契约。
`VERSION` | 活 | 构建、启动、依赖、版本或平台交付契约。
`bm25_index.py` | 死 | 与 src/bm25_index.py 字节一致；server、Docker 和测试均优先使用 src/ 版本，无独立调用路径。
`config.example.yaml` | 活 | 构建、启动、依赖、版本或平台交付契约。
`deploy/deploy.sh` | 活 | Docker、多租户或部署入口/配置。
`deploy/docker-compose.multi.yml` | 活 | Docker、多租户或部署入口/配置。
`deploy/docker-compose.testing.yml` | 活 | Docker、多租户或部署入口/配置。
`deploy/docker-compose.user.yml` | 活 | Docker、多租户或部署入口/配置。
`deploy/docker-compose.yml` | 活 | Docker、多租户或部署入口/配置。
`deploy/fetch_cloudflared.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`deploy/gen_update_manifest.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`deploy/multi_owner.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`deploy/owners.example.yaml` | 活 | Docker、多租户或部署入口/配置。
`docker-publish.yml` | 死 | 根目录工作流副本；GitHub 只执行 .github/workflows/ 下的同名文件，两份当前内容一致。
`entrypoint.sh` | 活 | 构建、启动、依赖、版本或平台交付契约。
`frontend/dashboard.html` | 活 | Dashboard 唯一前端源，由 web/dashboard.py 提供。
`frontend/favicon.svg` | 活 | Dashboard 静态资产。
`frontend/icon.svg` | 活 | Dashboard 静态资产。
`frontend/manifest.json` | 活 | Dashboard 静态资产。
`kernel/rust/ombre-kernel/Cargo.toml` | 活 | 独立 Rust 内核脚手架；pytest 校验，Cargo 可用时执行 cargo test；尚未接入 Python runtime。
`kernel/rust/ombre-kernel/src/lib.rs` | 活 | 独立 Rust 内核脚手架；pytest 校验，Cargo 可用时执行 cargo test；尚未接入 Python runtime。
`render.yaml` | 活 | 构建、启动、依赖、版本或平台交付契约。
`requirements-local.txt` | 活 | 构建、启动、依赖、版本或平台交付契约。
`requirements.txt` | 活 | 构建、启动、依赖、版本或平台交付契约。
`src/VERSION` | 活 | 构建、启动、依赖、版本或平台交付契约。
`src/backup_archive.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/bm25_index.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/bucket_manager.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/bucket_scoring.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/decay_engine.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/dehydrator.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/embedding_engine.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/embedding_outbox.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/errors.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/github_sync.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/import_memory.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ledger_mirror.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ledger_property.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ledger_replay.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/memory_messages.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/migrate_engine.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/migration_engine.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/__init__.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/acceptance/__init__.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/acceptance/contracts.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/acceptance/harness.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/adapters/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/adapters/bucket_adapter.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/adapters/migration.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/app/__init__.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/app/command_boundary_health.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/app/command_bridge.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/app/execution.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/app/legacy_runtime.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/app/legacy_wiring.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/app/neural_router.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/app/profiles.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/app/tool_output_contract.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/architecture/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/architecture/adr.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/architecture/auditor.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/architecture/code_standards.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/architecture/contracts.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/architecture/defaults.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/capabilities/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/capabilities/catalog.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/cluster/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/cluster/consensus.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/cluster/node.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/cluster/raft/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/cluster/raft/leader.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/cluster/raft/log.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/cluster/raft/quorum.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/cluster/replication/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/cluster/replication/apply.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/cluster/replication/catchup.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/cluster/replication/contract.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/cluster/safety/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/cluster/safety/integrity.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/collab/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/collab/graph.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/collab/merge_policy.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/decision/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/decision/debug.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/decision/ledger.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/decision/records.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/decision/replay.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/distributed/__init__.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/distributed/coordinator.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/distributed/membership.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/distributed/transport.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/domain/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/domain/boundary.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/domain/commands.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/domain/invariants.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/eventsourcing/__init__.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/eventsourcing/contracts.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/eventsourcing/kernel.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/fabric/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/fabric/log/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/fabric/log/snapshot.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/fabric/log/wal.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/fabric/storage/__init__.py` | 活 | Python 包边界；其子模块存在运行或测试引用。
`src/ombrebrain/fabric/storage/engine.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/kernel/__init__.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/kernel/context.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/kernel/errors.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/kernel/registry.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/maintenance/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/maintenance/migration_contract.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/maintenance/report.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/maintenance/vnext_coverage.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/microkernel/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/microkernel/contracts.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/microkernel/runtime.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/observability/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/observability/metrics.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/plugins/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/plugins/contracts.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/plugins/runtime.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/contracts.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/engine.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/formal_invariants.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/red_lines.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/static_surfaces.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/surfacing.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/update_policy.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/policy/vm.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/projection/__init__.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/ombrebrain/projection/audit_runtime.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/projection/auditor.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/projection/journal.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/projection/observation.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/projection/observers.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/projection/runtime.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/protocol/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/protocol/manifests.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/protocol/public_tools.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/protocol/schemas.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/resilience/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/resilience/recovery.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/resilience/scanner.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/retrieval/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/retrieval/context.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/retrieval/engine.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/retrieval/planner.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/retrieval/scoring.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/ombrebrain/version.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/projection_mirror.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/projection_sqlite.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/projection_vector.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/provider_detect.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/reclassify_api.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`src/retrieval_eval.py` | 活 | 未接入当前 server 生产链，但被 pytest 或架构验收直接/间接引用。
`src/server.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/_common.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/_runtime.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/anchor/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/anchor/core.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/breath/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/breath/_verbatim.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/breath/catalog.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/breath/feel.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/breath/importance.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/breath/search.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/breath/surface.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/dream/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/dream/candidates.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/dream/hints.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/dream/output.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/grow/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/grow/core.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/grow/shortpath.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/hold/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/hold/core.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/hold/feel.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/hold/pinned.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/i/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/i/core.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/plan/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/plan/core.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/trace/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/tools/trace/core.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/utils.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/vault_health.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/__init__.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/_shared.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/auth.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/buckets.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/config_api.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/dashboard.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/embedding.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/github.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/hooks.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/import_api.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/letters.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/meta.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/oauth.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/ollama_local.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/plans.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/search.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/system.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/tunnel.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/web/v3_debug.py` | 活 | 从 src/server.py 生产入口的静态导入链可达；动态路由和注册也按活代码计。
`src/write_memory.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tests.yml` | 死 | 根目录工作流副本；GitHub 只执行 .github/workflows/ 下的同名文件，两份当前内容一致。
`tests/__init__.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/conftest.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/dataset.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_adr_requirements_phase20.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_api_timeout_config.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_archive_collision.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_atomic_write.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_backup_archive.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_backup_import_safety.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_bm25_async_rebuild.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_breath_catalog.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_breath_verbatim_patch.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_code_standards_phase17.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_command_boundary_phase18.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_comprehensive.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_context_serialization_phase8b.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_crash_recovery_phase13.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_dashboard_diagnostics_panel.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_dashboard_import_preflight.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_dashboard_update_source.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_data_dir_persistence.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_datetime_metadata_normalization.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_dehydrator_output_icon.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_docker_tunnel_persistence.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_embedding_api_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_embedding_outbox.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_env_config_identity.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_feel_flow.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_fetch_cloudflared.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_formal_invariants_phase10.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_formal_invariants_phase8a.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_gen_update_manifest.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_github_backup_alarm.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_github_backup_manifest.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_github_sync_zero_commit.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_grow_items.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_hot_update_persistence.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_import_extraction_json.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_import_preflight.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_ledger_mirror_phase1.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_ledger_property_phase5b.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_ledger_replay_phase5a.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_letter_author_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_letter_read_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_list_all_cache.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_llm_quality.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_login_rate_limit.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_mcp_open_access_warning.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_memory_boundary_regressions.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_migration_contract_phase15.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_multi_owner_isolation.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_multi_owner_launcher.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_neural_tool_router_phase8c.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_oauth_refresh_token.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_observability_boundary_phase12.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_owner_identity.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_password_kdf.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_permanent_breath_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_pinned_quota_web_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_pinned_visibility_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_plugin_agency_boundary_phase11.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_priority4_confusion_cleanup.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_projection_mirror_phase2.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_public_tool_design_phase16.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_quota_counter_sync_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_red_lines_phase21.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_release_audit_regressions.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_replication_contract_phase14.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_retrieval_eval.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_retrieval_resilience.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_retrieval_scoring_phase9.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_rust_kernel_phase6a.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_scoring.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_security_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_sqlite_projection_phase2b.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_surface_context_compiler_phase19.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_surface_policy_phase3.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_system_diagnostics.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_tombstone_erasure_phase4.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_tool_output_contract_phase8d.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_touch_hotpath.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_trace_importance_regression.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_update_compile_guard.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_update_integrity.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_update_source_gate.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_architecture_audit.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_architecture_docs.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_bucket_adapter.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_capability_catalog.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_capability_microkernel.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_collab_graph.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_consensus.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_consistency_auditor.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_dashboard_debug_view.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_debug_web_api.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_decision_debug_service.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_decision_record.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_decision_replay.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_distributed_fabric.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_event_sourced_kernel.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_formal_acceptance_harness.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_kernel_registry.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_bucket_integration.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_command_bridge.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_component_attachment.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_execution_pipeline.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_module_profiles.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_runtime.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_server_wiring.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_tool_entrypoints.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_tools_runtime.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_legacy_web_integration.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_maintenance_report.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_memory_command_router.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_memory_event.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_memory_fabric.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_memory_invariants.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_migration.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_package.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_plugin_runtime.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_policy_contracts.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_policy_engine.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_policy_vm.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_projection_observers.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_projection_runtime.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_query_planner.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_raft_cluster.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_release_acceptance.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_release_docs.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_resilience_scanner.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_snapshot_catchup.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_static_surfaces.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_update_policy.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_v3_wal.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_vault_health.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_vector_projection_phase2c.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tests/test_vnext_preflight_report_phase22.py` | 活 | pytest 测试、fixture 或数据集；属于验证路径，不进入生产镜像。
`tools/backfill_embeddings.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/check_buckets.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/check_icloud_conflicts.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/clean_orphan_embeddings.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/debug_decision.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/diagnose_permanent_reads.py` | 存疑 | 独立 CLI 入口存在，但仓库内未找到外部调用或文档引用。
`tools/evaluate_retrieval.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/fix_unpinned_permanent.py` | 存疑 | 独立 CLI 入口存在，但仓库内未找到外部调用或文档引用。
`tools/migrate_feel_domain.py` | 存疑 | 独立 CLI 入口存在，但仓库内未找到外部调用或文档引用。
`tools/reclassify_domains.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/v3_health_report.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`tools/vnext_preflight.py` | 活 | 独立 CLI/维护入口，带 __main__ 且在文档、测试或构建中有引用。
`zbpack.json` | 活 | 构建、启动、依赖、版本或平台交付契约。

### 工具交叉验证

- Vulture 2.16（80% 置信阈值）：生产代码只报告两个兼容保留参数；纳入测试后另发现 2 个未使用 import 和 1 个未使用测试变量。
- Ruff F401/F841：发现 29 个未使用 import/局部变量，进入第二阶段处理。
- 此清单将在第三阶段结合真实覆盖率再校验；动态分支未执行不等于死代码。

## 第二阶段：代码质量与安全扫描

### 扫描结果

| 维度 | 结果 | 说明 |
|---|---:|---|
| Ruff | 150 -> 0 | 清理未使用 import/变量、单行复合语句，并为有意的延迟 import 与公开工具名 `I` 建立最小忽略规则。 |
| Vulture | 4 个高置信候选 | 3 个死副本与 1 个私有死函数已删除；兼容参数保留。 |
| Bandit | 高危 0，中危 10 -> 0 | 1 个无限连接等待已修；SQL 动态片段均来自固定 schema 白名单且值参数化；监听地址与可执行权限为部署契约并已显式标注。 |
| pip-audit | 0 个已知漏洞 | 基于 `requirements.txt` 当日解析结果。项目仍使用下限依赖，建议发版生成 constraints/lock 与 SBOM。 |
| Radon | 平均 C (11.79) | 存在多个高复杂度函数，见下方热点。 |

### 已修复

1. Plan 看板编辑路径调用不存在的 `_check_content_size`，特定请求会返回 500；改为显式导入并增加 400 回归测试。
2. Ollama 模型拉取原先 `timeout=None`；改为连接/写入/连接池有限、流式读取不限时，兼顾大模型下载与失联保护。
3. 导入文本和迁移 ZIP 原先先完整读入内存；增加 Content-Length 预检、流式累计上限及 multipart `limit + 1` 读取。文本导入默认上限 64MB，可由 `limits.max_import_upload_bytes` 配置；迁移 ZIP 沿用备份格式 512MB 上限。
4. 新增 `OMBRE_BIND_HOST`；Docker 默认行为仍为 `0.0.0.0`，裸机可设 `127.0.0.1` 限制为本机访问。
5. 日志最终兜底目录改为 `tempfile.gettempdir()`，消除硬编码 `/tmp` 的跨平台与权限问题。
6. 删除根目录重复的 `bm25_index.py`、`tests.yml`、`docker-publish.yml`，删除无调用的 `_verify_password_hash()`。
7. 清理生产与测试代码的无用 import/局部变量，并加入 `ruff.toml` 形成可重复质量门禁。

### 风险与建议

| 等级 | 位置 | 问题 | 建议 |
|---|---|---|---|
| 高 | `.github/workflows/tests.yml` | CI 只运行 2 个测试文件，仓库实际有 900+ 用例；大量分支不会在 PR 阶段阻断。 | 第三阶段得到覆盖率基线后改为完整 pytest + Ruff，并设置现实的覆盖率门槛。 |
| 高 | `src/ombrebrain/fabric/log/wal.py` | `next_index()` 与 `append()` 是两次无锁读写；同进程并发或多个实例可写出重复 index/断裂 checksum。 | 第四阶段做并发红队；采用同路径共享锁并把定位末项、分配 index、追加写入放进一个临界区。 |
| 中 | `src/web/system.py` | `build_system_diagnostics` 圈复杂度 138，文件 1415 行；诊断项、I/O 与展示数据耦合。 | 按 diagnostics domain 拆 provider，保留单一聚合器。 |
| 中 | `src/tools/breath/surface.py` | `surface_default` 圈复杂度 95；预算、排序、随机浮现和策略混在一个函数。 | 拆为候选选择、原子预算、被动联想和渲染四个纯函数/服务。 |
| 中 | `src/tools/trace/core.py` | 圈复杂度 73；字段校验、状态迁移、归档与副作用耦合。 | 引入 typed update command + validator；存储层只应用规范化命令。 |
| 中 | `src/bucket_manager.py` | 1962 行；`create/update/search` 复杂度分别 59/49/45，同步文件 I/O 位于 async 调用链。 | 分离 metadata repository、索引协调器与检索器；批量磁盘工作放入 `asyncio.to_thread`。 |
| 中 | `frontend/dashboard.html` | 8298 行、约 432KB，HTML/CSS/JS 单文件。 | 逐步拆 ES modules；先从 transport/import/diagnostics 三块开始。 |
| 中 | `web` 包 | `web/__init__.py` eager import 全部 18 个路由模块，与 `_shared` 全局注入形成强耦合环。 | 路由 manifest 延迟导入；依赖通过显式 context 传入。 |
| 低 | 多处容错分支 | Bandit 仍报告 60 个低风险项，多数为 `except/pass`。 | 后续按“静默是否会隐藏数据错误”分类，至少记录 debug/warning 或附明确降级状态。 |

### 第二阶段验证

- `ruff check src tools deploy tests --no-cache`：通过。
- `bandit -r src tools deploy -ll -ii -q`：通过（高/中风险 0）。
- `pip-audit -r requirements.txt`：无已知漏洞。
- 定向 pytest：133 passed，7 skipped。

## 第三阶段：测试与覆盖率

### 执行环境与总结果

- 审计镜像：`ombre-brain-code-audit:local`，Python 3.12.13。
- 生产验证镜像：`ombre-brain-code-health:local`；独立网络 `ob-health-net`、独立命名卷 `ob-health-data`，未挂载或读取用户真实 buckets。
- 全量命令：`pytest tests -q --asyncio-mode=auto --cov=src --cov-report=term --cov-fail-under=60`。
- 结果：**936 passed，37 skipped，0 failed**；总行覆盖率 **65.03%**（17626 statements，6164 missing）。
- 37 个跳过项中，30 个是需要显式 Docker MCP URL 的集成用例，7 个是项目原有的条件测试；30 个 Docker 用例已在隔离栈中另行全部执行通过。

### 12 个 MCP 工具真实集成验证

测试通过 streamable HTTP 完成 JSON-RPC `initialize`、`tools/list` 和 `tools/call`，不是直接调用 Python 内部函数。LLM 依赖使用确定性 OpenAI-compatible stub，持久化使用隔离 Docker 卷。

| 工具 | 验证行为 | 结果 |
|---|---|---|
| `breath` | 查询命中并返回已存原文 | 通过 |
| `hold` | 写入短记忆并返回 bucket id | 通过 |
| `grow` | 长内容拆分、持久化并返回结果 | 通过 |
| `trace` | 更新已有记忆元数据 | 通过 |
| `anchor` | 标记长期锚定 | 通过 |
| `release` | 解除锚定但不物理删除记忆 | 通过 |
| `pulse` | 返回系统与桶统计 | 通过 |
| `plan` | 创建 active plan | 通过 |
| `letter_write` | 逐字写入 letter | 通过 |
| `letter_read` | 按条件读回 letter | 通过 |
| `I` | 写入并读取自我描述 | 通过 |
| `dream` | 返回近期完整记忆 | 通过 |

- 工具清单严格断言为文档约定的 12 个，无缺失、无额外暴露。
- 异常路径覆盖 8 类：空 `hold/grow`、不存在的 `trace/anchor/release` id、空 plan、letter 缺 author、`I` 非法 aspect；均返回可解释错误，服务未崩溃。
- 红队扩展覆盖 prompt 注入原文、路径穿越形态 id、全局 HTTP body 上限、grow 总量/条目上限、plan/letter/I 单桶上限与 8 会话并发 hold。
- 修复 `I` 过去接受任意 aspect 的问题；现在仅允许 `nature/values/patterns/limits/becoming/uncertainty/stance`。
- 最终重启持久化：重启前 11 buckets，重启后 11 buckets，结果一致；内容锁残留文件 0。

### 新增回归覆盖

- `tests/test_code_health_regressions.py`：Plan 超大编辑、Ollama 超时契约、流式导入上限、multipart 越界、`I` aspect 校验。
- `tests/test_mcp_tools_docker_integration.py`：12 工具的真实 MCP 行为与异常路径。
- `tests/mcp_llm_stub.py`：仅供测试的确定性 LLM HTTP stub，不进入生产启动路径。
- `tests/test_red_team_regressions.py`：WAL 线程/进程并发、跨事件循环同正文互斥、输入上限、非有限数值、prompt 数据边界、ASGI 限额与 CLI frontmatter 注入。

### 覆盖率盲区

| 覆盖率 | 模块 | 说明 |
|---:|---|---|
| 0% | `src/server.py` | 导入即初始化服务，现有单测绕过入口；真实 Docker MCP 测试覆盖了行为但未并入 coverage 进程。 |
| 0% | `src/reclassify_api.py` | 旧重分类 API 包装层没有直接测试。 |
| 11%-20% | `src/tools/breath/feel.py`、`src/tools/anchor/core.py`、`src/web/auth.py`、`src/web/buckets.py`、`src/web/letters.py` | 分支密集或依赖路由上下文，异常/权限分支覆盖不足。 |
| 23%-39% | 多个 `src/web/*`、`src/import_memory.py`、`src/migration_engine.py` | API 业务层与框架路由耦合，难以低成本隔离测试。 |
| 55% | `src/write_memory.py` | 已新增结构化 frontmatter/原子写安全测试；交互式 CLI 分支仍未自动化。 |

### CI 门禁修正

- `.github/workflows/tests.yml` 从只跑 2 个测试文件改为运行完整 `tests/`。
- 新增 Ruff 门禁、coverage XML 和 `--cov-fail-under=60`。
- `main` 与 `testing` 的 push/PR 都会触发；工作流会自动构建隔离 Docker 栈并执行 30 条 MCP 集成测试。
- CI YAML 已解析校验，Ruff 与本地等价的完整 pytest 命令均通过。

### 测试环境注意项

容器入口从持久卷的 `/app/buckets/_app` 运行代码。若仅重建镜像却不改变版本标识，同名持久卷可能继续运行旧源码快照；本次首次集成测试因此捕获到旧实现。清空本次隔离卷后确认运行源码与镜像一致。正式发布必须同步更新版本号，测试中则应使用新卷或显式校验运行目录源码指纹。

## 第四阶段：红蓝对抗

### 红队复现与蓝队结果

| 攻击面 | 修复前实测 | 蓝队修复 | 修复后实测 |
|---|---|---|---|
| WAL 并发写 | 240 次线程追加仅 3 次返回成功、237 次报错，产生重复 index，replay 校验链断裂。 | 同路径进程内共享锁 + 跨进程 sidecar 文件锁；分配 index、checksum 与 append 放入同一临界区。 | 240/240 成功、0 报错、240 个唯一连续 index；线程与 4 进程回归均通过。 |
| 同正文并发 `hold` | 8 个独立 MCP 会话偶发创建 2 个逐字相同的桶。 | 跨线程/事件循环 future 队列 + 原子内容锁文件 + 新建前直接扫描 Markdown 真源 exact match，绕开陈旧缓存。 | 8 会话只生成 1 个桶；完整集成通过后另重复 5 轮，全部收敛为 1。 |
| 超大 MCP body | 5MB 无效 body 被完整接收、解析后才返回 400。 | 4MB ASGI 流式/Content-Length 双门禁，工具层另设 grow/query/metadata/item 上限。 | 4MB+1 在 JSON-RPC 解析前返回 413；grow 2MB+1、101 items 和 50KB+1 单桶均被拒绝且无写入。 |
| 非有限数值 | `NaN` 可进入 valence；`±Inf` importance 抛 `OverflowError`；正数配置 helper 接受 NaN/Inf。 | storage/config/retrieval 边界统一 `math.isfinite`，非法值回退明确默认值。 | 持久化元数据均为有限数；异常调用不崩溃。 |
| Prompt 注入记忆 | `breath` 必须逐字返回正文，但外层没有“数据而非指令”的直接标记。 | 只在元数据 header 增加 `[content_role:stored_memory_data] [instructions:false]`；正文一字不动。 | 恶意 imperative 文本 exact equality 通过，正文没有改写、摘要或待办生成。 |
| CLI frontmatter 注入 | `write_memory.py` 直接拼 YAML，name/domain/tag 中换行可注入字段；写入非原子。 | 改用 `frontmatter.Post` 结构化序列化和公共 `atomic_write_text`；限制元数据与有限数值。 | 注入字符串保持为字段值，不能生成 `pinned/type` 等新字段；无临时残留。 |
| 路径穿越形态输入 | `trace(bucket_id='../../...')` 作为 id 扫描，未发现越界读写；`safe_path()` 已用 `Path.is_relative_to`。 | 保留原有路径防护，新增真实 MCP 回归。 | 返回“未找到记忆桶”，无宿主路径访问。 |

### 蓝队实现摘要

1. `src/web/request_limits.py` 提供纯 ASGI MCP body 限额，不使用会破坏 SSE 的 `BaseHTTPMiddleware`。
2. `config.example.yaml` 新增 `max_mcp_request_bytes/max_grow_input_bytes/max_query_bytes/max_metadata_bytes/max_grow_items`；0 明确表示禁用，修正原先 `max_bucket_bytes/max_pinned=0` 被 `or default` 覆盖的问题。
3. BucketManager 成为最后一道边界：单桶大小、有限数值、tags/domain 数量和长度均集中收敛；exact-content 可直接读 Markdown 真源。
4. `breath` 仍遵守逐字保真与原子 token 预算；安全标记仅位于正文外，不修改、删除或迁移任何记忆。
5. CI 现在运行 Ruff、全量 pytest、60% coverage 门槛以及真实 12 工具 Docker MCP 测试栈。

### 残余风险

- Prompt 数据标记属于纵深防御，不能数学保证所有上层模型都忽略记忆中的命令式文本；调用方仍应把工具输出视作不可信数据。为了遵守“记忆不可改写”，本项目不会通过删改正文来消毒。
- `src/server.py` 在 coverage 进程中仍是 0%，因为导入会装配全局服务；其启动与 12 工具行为已由独立 Docker 进程覆盖，但 coverage.py 无法合并该进程数据。
- `reclassify_api.py` 仍为 0%，旧包装入口缺直接测试；Web 路由整体覆盖仍偏低，是下一轮最明确的测试债务。
- 依赖仍以最低版本约束为主，Docker 构建会解析当时最新版本；建议发版增加 lock/constraints 与 SBOM，降低供应链漂移。
- 大文件和高复杂度热点仍在：`bucket_manager.py`、`web/system.py`、`breath/surface.py`、Dashboard 单文件。此次只修实证风险，没有借审计大改架构。

### 审计新增文件状态

| 文件路径 | 状态 | 说明 |
|---|---|---|
| `ruff.toml` | 活 | CI 与本地静态检查配置。 |
| `src/web/request_limits.py` | 活 | `server.py` 在 HTTP/SSE 启动时装配的 MCP 请求体中间件。 |
| `tests/mcp_llm_stub.py` | 活 | Docker 集成测试的确定性 OpenAI-compatible stub。 |
| `tests/test_code_health_regressions.py` | 活 | 第二阶段修复回归。 |
| `tests/test_mcp_tools_docker_integration.py` | 活 | 12 工具真实 HTTP 集成与红队用例。 |
| `tests/test_red_team_regressions.py` | 活 | 第四阶段并发、安全、异常与边界回归。 |
| `docs/CODE_HEALTH_AUDIT_2026-07-12.md` | 活 | 本次四阶段审计报告。 |

### 最终验证

- 全量 pytest + coverage：**936 passed，37 skipped，0 failed；65.03%**。
- 隔离 Docker MCP：**30 passed，0 failed**；12 个工具逐一覆盖。
- 并发 hold 压测：8 会话/轮，额外连续 5 轮全部单桶收敛。
- WAL 攻击重测：240 successes，0 errors，240 unique/contiguous indexes。
- Ruff：通过；Bandit 高/中风险：0；pip-audit：0 个已知漏洞。
- Docker 重启：11 -> 11 buckets；内容锁残留：0。
- 未提交、未推送；未访问或修改用户真实记忆数据。
