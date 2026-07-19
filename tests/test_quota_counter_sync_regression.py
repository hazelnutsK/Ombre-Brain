"""配额计数器同步回归测试 —— 按用户反馈的精确复现路径走。

反馈场景（v2.3.22，Render）：
1. pinned：取消钉选到 17 个后仍订不上新的，报「有 24 个 pin」
   → 旧根因：取消钉选后残留的 type=permanent 也被算进 pinned 配额。
2. importance≥9：trace(bucket_id, importance=7) 降级后，hold(importance=9)
   仍报「已有 84 条 ≥9（硬上限 24）」自动降为 8；实际 breath 只剩 18 条
   → 旧根因：pinned/protected（importance 锁 10）也被算进 ≥9 配额，且计数不实时。

当前实现的两条硬保证（本文件锁死，防止回退）：
- 配额计数每次实时从盘上数（无缓存计数器），trace 改完立即生效；
- pinned 只数 metadata.pinned，type=permanent 不占 pinned 配额；
  importance≥9 配额排除 pinned/protected。
"""
import asyncio
from unittest.mock import MagicMock

import pytest

import tools._runtime as rt
from tools._common import (
    count_high_importance,
    count_pinned,
    enforce_high_importance_quota,
    enforce_pinned_quota,
    merge_or_create,
)
from tools.trace.core import trace_core


class EchoDehydrator:
    async def dehydrate(self, content, meta=None):
        return content


def install_runtime(bucket_mgr, limits=None):
    rt.config = {"surfacing": {}, "limits": limits or {}}
    rt.bucket_mgr = bucket_mgr
    rt.dehydrator = EchoDehydrator()
    rt.logger = MagicMock()
    rt.fire_webhook = None
    rt.mark_op = None


class StaticBucketManager:
    """Minimal counter fixture for legacy/imported physical row shapes."""

    def __init__(self, rows):
        self.rows = rows

    async def list_all(self, include_archive=False):
        assert include_archive is False
        return list(self.rows)


def _quota_row(
    bucket_id: str,
    *,
    importance=9,
    bucket_type="dynamic",
    pinned=False,
    protected=False,
    dont_surface=False,
):
    return {
        "id": bucket_id,
        "metadata": {
            "importance": importance,
            "type": bucket_type,
            "pinned": pinned,
            "protected": protected,
            "dont_surface": dont_surface,
        },
    }


# ------------------------------------------------------------
# ① pinned 配额：trace 解钉后必须立刻能钉新的
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_unpin_via_trace_frees_pinned_quota(bucket_mgr):
    # 上限设小（3）让测试轻量；语义与默认 20 一致
    install_runtime(bucket_mgr, limits={"max_pinned": 3})

    ids = []
    for i in range(3):
        ids.append(await bucket_mgr.create(content=f"核心准则 {i}", pinned=True))

    # 满额：钉新桶被拒（enforce 返回 False = 走普通桶）
    assert await count_pinned() == 3
    assert await enforce_pinned_quota(True) is False

    # 复现步骤：trace(bucket_id, pinned=0) 解钉一个
    await trace_core(ids[0], pinned=0)

    # 计数必须实时下降，且立刻能钉新的——不允许残留旧计数
    assert await count_pinned() == 2
    assert await enforce_pinned_quota(True) is True


@pytest.mark.asyncio
async def test_trace_unpin_reserves_new_high_importance_slot(
    bucket_mgr,
    monkeypatch,
):
    """A pinned 10 starts consuming the ordinary high quota when unpinned."""
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 1)

    await bucket_mgr.create(content="existing high slot", importance=9)
    pinned_id = await bucket_mgr.create(content="will be unpinned", pinned=True)

    await trace_core(pinned_id, pinned=0)

    unpinned = await bucket_mgr.get(pinned_id)
    assert unpinned["metadata"]["pinned"] is False
    assert unpinned["metadata"]["type"] == "dynamic"
    assert unpinned["metadata"]["importance"] == 8
    assert await count_high_importance() == 1


@pytest.mark.asyncio
async def test_trace_can_unpin_and_lower_importance_atomically(bucket_mgr):
    install_runtime(bucket_mgr)
    pinned_id = await bucket_mgr.create(content="lower while unpinning", pinned=True)

    result = await trace_core(pinned_id, pinned=0, importance=7)

    unpinned = await bucket_mgr.get(pinned_id)
    assert "pinned=False" in result
    assert "importance=7" in result
    assert unpinned["metadata"]["pinned"] is False
    assert unpinned["metadata"]["type"] == "dynamic"
    assert unpinned["metadata"]["importance"] == 7


@pytest.mark.asyncio
async def test_permanent_type_does_not_occupy_pinned_quota(bucket_mgr):
    """旧根因锁死：解钉后桶留在 permanent 类型/目录，不得再占 pinned 配额。

    （用户实际 17 个 pin 却被报 24：多出来的就是这类残留。）"""
    install_runtime(bucket_mgr, limits={"max_pinned": 3})

    # 2 个真 pinned + 2 个曾 pinned 后解钉的（type 仍是 permanent）
    await bucket_mgr.create(content="真钉 A", pinned=True)
    await bucket_mgr.create(content="真钉 B", pinned=True)
    for i in range(2):
        bid = await bucket_mgr.create(content=f"曾钉 {i}", pinned=True)
        await trace_core(bid, pinned=0)

    # 只数 metadata.pinned=True 的：2，不是 4
    assert await count_pinned() == 2
    # 2 < 3 → 还能钉
    assert await enforce_pinned_quota(True) is True


@pytest.mark.asyncio
async def test_pinned_counter_normalizes_booleans_and_logical_ids():
    pinned = _quota_row("pinned", pinned=True, importance=10)
    quoted_false = _quota_row(
        "quoted-false", pinned="false", importance=10
    )
    archived = _quota_row("archived", pinned=True, importance=10)
    archived["metadata"]["type"] = "archived"
    install_runtime(
        StaticBucketManager(
            [pinned, pinned, quoted_false, archived]
        )
    )

    assert await count_pinned() == 1


# ------------------------------------------------------------
# ② importance≥9 配额：trace 降级后计数必须实时同步
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_trace_demote_frees_high_importance_quota(bucket_mgr, monkeypatch):
    install_runtime(bucket_mgr)
    # 上限收小到 3，复刻「超限自动降级」再「trace 释放后恢复」的完整链路
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 3)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 3)

    ids = []
    for i in range(3):
        ids.append(await bucket_mgr.create(content=f"重要记忆 {i}", importance=9))

    # 满额：新 hold(importance=9) 被自动降级为 8（OB-I001 行为）
    assert await count_high_importance() == 3
    assert await enforce_high_importance_quota(9) == 8

    # 复现步骤：trace(bucket_id, importance=7) 降级一条
    await trace_core(ids[0], importance=7)

    # 计数实时同步 → 新的 importance=9 不再被误降
    assert await count_high_importance() == 2
    assert await enforce_high_importance_quota(9) == 9


@pytest.mark.asyncio
async def test_pinned_not_counted_in_high_importance_quota(bucket_mgr):
    """旧根因锁死：pinned/protected（importance 锁 10）不占 ≥9 配额。

    （用户实际 18 条 ≥9 却被报 84：虚高部分就是 pinned/permanent 混入。）"""
    install_runtime(bucket_mgr)

    await bucket_mgr.create(content="钉住的核心", pinned=True)      # importance 锁 10
    await bucket_mgr.create(content="普通高重要", importance=9)

    assert await count_high_importance() == 1


# ------------------------------------------------------------
# ③ trace 不能绕过 importance≥9 配额（此前只有 hold 的创建路径检查过）
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_trace_promote_respects_high_importance_quota(bucket_mgr, monkeypatch):
    """回归锁死：trace(bucket_id, importance=9) 也要经过硬上限检查。"""
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 3)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 3)

    ids = [await bucket_mgr.create(content=f"普通桶 {i}", importance=5) for i in range(4)]

    for bid in ids[:3]:
        await trace_core(bid, importance=9)
    assert await count_high_importance() == 3

    # 第 4 个再通过 trace 提到 9 应被自动降级为 8，而不是把配额冲破 3
    await trace_core(ids[3], importance=9)
    bucket = await bucket_mgr.get(ids[3])
    assert bucket["metadata"]["importance"] == 8
    assert await count_high_importance() == 3


@pytest.mark.asyncio
async def test_trace_re_setting_already_high_importance_is_not_self_penalized(bucket_mgr, monkeypatch):
    """已经占着配额的桶改自己的 importance（仍 ≥9）不该被自己的存在误挡。"""
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 1)

    bid = await bucket_mgr.create(content="唯一高重要", importance=9)
    assert await count_high_importance() == 1

    await trace_core(bid, importance=10)
    bucket = await bucket_mgr.get(bid)
    assert bucket["metadata"]["importance"] == 10


# ------------------------------------------------------------
# ④ letter 固定 importance=10，不该占 ≥9 配额（letter 永不衰减/合并，
#    不是"抢到了高重要度名额"的动态记忆）
# ------------------------------------------------------------

@pytest.mark.asyncio
async def test_letter_does_not_occupy_high_importance_quota(bucket_mgr):
    install_runtime(bucket_mgr)

    await bucket_mgr.create(
        content="给未来自己的一封信", importance=10, bucket_type="letter",
    )
    await bucket_mgr.create(content="普通高重要", importance=9)

    # 只数普通桶那一条，letter 不占位
    assert await count_high_importance() == 1


@pytest.mark.asyncio
async def test_high_importance_counter_matches_breath_audit_scope():
    """Regression: the quota warning must not report 89 when only 18 are auditable."""
    rows = [
        *[_quota_row(f"ordinary-{index}") for index in range(18)],
        *[
            _quota_row(f"forgotten-{index}", dont_surface=True)
            for index in range(50)
        ],
        *[_quota_row(f"feel-{index}", bucket_type="feel") for index in range(11)],
        *[_quota_row(f"plan-{index}", bucket_type="plan") for index in range(10)],
    ]
    install_runtime(StaticBucketManager(rows))

    assert len(rows) == 89
    assert await count_high_importance() == 18


@pytest.mark.asyncio
async def test_high_importance_counter_counts_each_logical_bucket_id_once():
    canonical = [_quota_row(f"bucket-{index}") for index in range(12)]
    install_runtime(StaticBucketManager(canonical + canonical))

    assert await count_high_importance() == 12


@pytest.mark.asyncio
async def test_high_importance_counter_normalizes_legacy_metadata_per_row():
    visible = _quota_row("visible")
    text_false = _quota_row("text-false", pinned="false")
    text_true = _quota_row("text-true", pinned="true")
    permanent = _quota_row("permanent", bucket_type="permanent", importance="10")
    corrupt = _quota_row("corrupt", importance="not-a-number")
    tombstone = _quota_row("tombstone")
    tombstone["metadata"]["tombstone"] = True
    deleted = _quota_row("deleted")
    deleted["metadata"]["deleted_at"] = "2026-01-01T00:00:00Z"
    install_runtime(
        StaticBucketManager(
            [visible, text_false, text_true, permanent, corrupt, tombstone, deleted]
        )
    )

    # Explicit unpinned permanent is a first-class visible memory and counts;
    # malformed/terminal rows do not zero the rest of the scan.
    assert await count_high_importance() == 3


@pytest.mark.asyncio
async def test_trace_restore_hidden_high_importance_reserves_slot(
    bucket_mgr,
    monkeypatch,
):
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 1)

    await bucket_mgr.create(content="existing visible high", importance=9)
    hidden_id = await bucket_mgr.create(content="hidden high", importance=10)
    await bucket_mgr.update(hidden_id, dont_surface=True)

    await trace_core(hidden_id, dont_surface=0)

    restored = await bucket_mgr.get(hidden_id)
    assert restored["metadata"]["dont_surface"] is False
    assert restored["metadata"]["importance"] == 8
    assert await count_high_importance() == 1


@pytest.mark.asyncio
async def test_merge_promotion_cannot_bypass_high_importance_cap(
    bucket_mgr,
    monkeypatch,
):
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 1)

    await bucket_mgr.create(content="existing visible high", importance=9)
    target_id = await bucket_mgr.create(content="merge target", importance=5)
    target = await bucket_mgr.get(target_id)
    target["score"] = 100.0

    async def find_target(*_args, **_kwargs):
        return [target]

    monkeypatch.setattr(bucket_mgr, "search", find_target)
    merged_id, merged, _warning = await merge_or_create(
        content="new merged event",
        tags=[],
        importance=9,
        domain=[],
        valence=0.5,
        arousal=0.3,
        raw_merge=True,
        source_tool="hold",
    )

    persisted = await bucket_mgr.get(target_id)
    assert merged is True
    assert merged_id == target_id
    assert persisted["metadata"]["importance"] == 8
    assert await count_high_importance() == 1


@pytest.mark.asyncio
async def test_concurrent_merge_promotions_preserve_both_events_and_one_slot(
    bucket_mgr,
    monkeypatch,
):
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 1)
    target_id = await bucket_mgr.create(content="merge base", importance=5)

    async def find_target(*_args, **_kwargs):
        row = await bucket_mgr.get(target_id)
        row["score"] = 100.0
        return [row]

    monkeypatch.setattr(bucket_mgr, "search", find_target)

    async def merge_event(text):
        return await merge_or_create(
            content=text,
            tags=[],
            importance=9,
            domain=[],
            valence=0.5,
            arousal=0.3,
            raw_merge=True,
            source_tool="hold",
        )

    results = await asyncio.gather(
        merge_event("concurrent event A"),
        merge_event("concurrent event B"),
    )

    persisted = await bucket_mgr.get(target_id)
    assert all(result[:2] == (target_id, True) for result in results)
    assert "concurrent event A" in persisted["content"]
    assert "concurrent event B" in persisted["content"]
    assert persisted["metadata"]["importance"] == 9
    assert await count_high_importance() == 1
