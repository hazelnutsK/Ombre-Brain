# 待办：v3_debug / ombrebrain 接入层尚未真正同步

记录时间：2026-06-30

## 背景

仓库根目录（`/embedding_engine.py`、`/web/`、`/tools/` 等）和 `src/` 是两棵独立演化
的代码树。`src/` 才是生产实际运行的那棵——`Dockerfile` 只 `COPY src/`，
`entrypoint.sh` 执行的是 `src/server.py`。

提交 `71a145b 发布版本：v2.4.0 接入层更新` 把一整套 v3 运行时埋点代码
（`attach_v3_runtime`、`record_v3_tool_event`、`run_v3_(async_)operation` 等）
写进了仓库根目录，而不是 `src/`，且从未同步过去。这批代码全部依赖
`import ombrebrain`，但 `ombrebrain/` 这个包（event sourcing / policy /
raft cluster / retrieval planner 等 v3 架构核心，~70 个文件）只存在于
`src/ombrebrain/`（提交 `330e140` 引入）。也就是说：

- **仓库根目录那套 v3 接入层代码，若按根目录路径独立运行会在 import 阶段
  直接 `ModuleNotFoundError`，从未真正跑通过、也从未上线过。**
- Dashboard 前端的 "2.4.0 Debug / Replay" 面板调用的
  `/api/v3/debug/{decisions,decision/{id},replay/{id}}`，对应的后端实现
  `web/v3_debug.py` 此前只存在于根目录，未被打进生产镜像 → 面板表现为
  404（路由都不存在）。

## 已做的事（2026-06-30）

把 `web/v3_debug.py`（根目录版本）原样复制进 `src/web/v3_debug.py`，并在
`src/web/__init__.py` 的 `register_all()` 里注册它。这个文件本身写得很
干净——用 `getattr(sh, "v3_runtime", None)` 探测，没有就直接返回
`{"available": False}"`，**不会因为 v3_runtime 缺失而报错**。

合并后效果：路由不再 404，但所有 `/api/v3/debug/*` 请求都会诚实返回
`available: False`（因为 `src/web/_shared.py` 还没有 `v3_runtime` 这个
属性，`src/server.py` 也从未实例化/挂载过 `ombrebrain` 的 runtime）。

**同日补充**：既然面板打开就是空列表（没数据，但也不报错），先把
`frontend/dashboard.html` 里 "2.4.0 Debug / Replay" 这个 Tab 入口注释掉
（搜 `v3-debug tab 暂时隐藏` 能找到那段），避免用户点进去看到一个永远
空白的面板而困惑。后端路由 `/api/v3/debug/*` 本身没动，仍然注册着；
等 `v3_runtime` 真正接入后，取消那行注释即可恢复入口，不需要再补代码。

## 还没做、需要决策的事

1. **`src/ombrebrain/` 这套 v3 架构核心要不要真正接入 `src/server.py`？**
   这是个独立、大范围的架构决策（涉及 event sourcing、决策回放、raft
   cluster 等），不是简单的文件搬运。在没有人明确决定"现在要不要让 v3
   runtime 在生产跑起来"之前，不要尝试盲目把根目录那批
   `attach_v3_runtime` 埋点钩子也搬进 `src/`——它们全部耦合于同一条
   `ombrebrain` 依赖链，孤立搬运任何一个文件都可能引入 import 错误或
   半生效的状态。

2. **仓库根目录这批与 `src/` 重名的文件**（`server.py`、
   `embedding_engine.py`、`bucket_manager.py`、`decay_engine.py`、
   `dehydrator.py`、`github_sync.py`、`import_memory.py`、
   `migrate_engine.py`、`migration_engine.py`、`web/`、`tools/` 的大部分
   内容）该如何处理，尚未决定。已确认的事实：
   - 这些根目录文件普遍**缺少**万世 2026-06-30 提交的 3 个 bug 修复
     （pin 配额检查、breath/dream pinned 桶可见性兜底、
     embedding 模型名/维度归一化）。
   - 在仓库根目录直接跑 `pytest tests/`（而不是 `cd src && pytest`）
     时，Python 会因为根目录这些重名模块排在 `sys.path` 前面而优先
     加载它们，导致测试结果失真（详见下一条）。

3. **`sys.path` 假阳性问题**：只要仓库根目录还留着这些重名 `.py`
   文件，在根目录直接跑 `pytest` 就有路径风险（`tests/__init__.py`
   存在会让 pytest 把根目录插到 `sys.path` 前面，盖过 `tests/conftest.py`
   里 `sys.path.insert(0, src)` 的效果）。修复方向二选一：
   - 删除/迁出根目录这些重名旧文件（如果确认它们已死，src/ 完全覆盖
     了它们的职责）；
   - 或调整 `tests/conftest.py`，确保 `src/` 路径在任何情况下都排在
     仓库根目录之前。
   在第 2 点的"根目录文件去留"决策做出之前，建议团队成员**始终在
   `src/` 目录内或显式加 `--rootdir=src` 跑测试**，不要在仓库根目录
   直接跑 `pytest tests/`。

## 谁应该看到这个文件

任何下一次碰 `web/v3_debug.py`、`ombrebrain/`、或者发现 Dashboard 的
"2.4.0 Debug/Replay" 面板行为异常的人。在动手"修复"或"同步"两棵树之前，
先读这份文档，避免重复踩坑或盲目合并引入更深的依赖混乱。
