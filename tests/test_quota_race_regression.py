"""并发配额竞态回归测试 —— 验证 _quota_turn 真的把「先数后写」串行化了。

找茬会话复现场景（2026-07-15）：
- pinned/anchor/importance≥9 配额检查全是「count() → 决定 → 之后才写」两步走，
  中间没有锁跨越两步。两个并发请求都能在对方提交前读到同一个「未满」快照，
  一起通过检查后各自写入，把硬上限冲破。

本文件用 asyncio.gather 真实并发触发这条路径，锁死「即使并发也不能破配额」。
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import asyncio
import pytest

import tools._runtime as rt
from tools._common import (
    _quota_turn,
    count_high_importance,
    count_pinned,
    merge_or_create,
)
from tools.hold.pinned import store_pinned
from tools.trace.core import trace_core


class EchoDehydrator:
    """analyze() 立即返回，不引入真实延迟——竞态窗口完全靠调度器交错制造。"""

    async def analyze(self, content):
        return {
            "domain": ["未分类"], "valence": 0.5, "arousal": 0.3,
            "tags": [], "suggested_name": "",
        }

    async def dehydrate(self, content, meta=None):
        return content


def install_runtime(bucket_mgr, limits=None):
    rt.config = {"surfacing": {}, "limits": limits or {}}
    rt.bucket_mgr = bucket_mgr
    rt.dehydrator = EchoDehydrator()
    rt.logger = MagicMock()
    rt.fire_webhook = None
    rt.mark_op = None


@pytest.mark.asyncio
async def test_concurrent_hold_pinned_does_not_exceed_cap(bucket_mgr, monkeypatch):
    install_runtime(bucket_mgr, limits={"max_pinned": 3})
    monkeypatch.setattr("tools._common._PINNED_SOFT_GAP", 0)

    # 已有 2/3 pinned，剩 1 个名额；5 个并发请求同时抢这 1 个名额。
    for i in range(2):
        await bucket_mgr.create(content=f"已钉 {i}", pinned=True)

    results = await asyncio.gather(*[
        store_pinned(
            content=f"并发抢钉 {i}", extra_tags=[], valence=0.5, arousal=0.3,
            why_remembered="",
        )
        for i in range(5)
    ])

    final_count = await count_pinned()
    assert final_count == 3, f"pinned 配额被冲破：cap=3 实际={final_count}"
    succeeded = [r for r in results if r.startswith("📌")]
    assert len(succeeded) == 1, f"应该只有 1 个并发请求真正钉成功，实际 {len(succeeded)} 个: {results}"


@pytest.mark.asyncio
async def test_concurrent_trace_promote_does_not_exceed_cap(bucket_mgr, monkeypatch):
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 3)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 3)

    # 已有 2/3 高重要度，剩 1 个名额；5 个并发 trace(importance=9) 同时抢。
    for i in range(2):
        await bucket_mgr.create(content=f"已高重要 {i}", importance=9)
    ids = [await bucket_mgr.create(content=f"普通桶 {i}", importance=5) for i in range(5)]

    await asyncio.gather(*[trace_core(bid, importance=9) for bid in ids])

    final_count = await count_high_importance()
    assert final_count == 3, f"importance≥9 配额被冲破：cap=3 实际={final_count}"

    promoted = 0
    for bid in ids:
        b = await bucket_mgr.get(bid)
        if b["metadata"]["importance"] == 9:
            promoted += 1
    assert promoted == 1, f"应该只有 1 个并发 trace 真正提到 9，实际 {promoted} 个"


@pytest.mark.asyncio
async def test_concurrent_unhide_and_promote_cannot_bypass_high_cap(
    bucket_mgr,
    monkeypatch,
):
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 1)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 1)

    await bucket_mgr.create(content="existing visible high", importance=9)
    target_id = await bucket_mgr.create(content="hidden low target", importance=5)
    await bucket_mgr.update(target_id, dont_surface=True)

    await asyncio.gather(
        trace_core(target_id, dont_surface=0),
        trace_core(target_id, importance=9),
    )

    target = await bucket_mgr.get(target_id)
    target_meta = target["metadata"]
    visible_high = (
        not bool(target_meta.get("dont_surface"))
        and int(target_meta.get("importance") or 0) >= 9
    )
    assert visible_high is False
    assert await count_high_importance() == 1


@pytest.mark.asyncio
async def test_cancelled_quota_waiter_does_not_poison_or_open_the_turn(
    monkeypatch,
):
    # Exercise the in-process Future chain directly.  Without a base_dir there
    # is no filesystem lock to hide a broken cancellation hand-off.
    monkeypatch.setattr(rt, "bucket_mgr", SimpleNamespace(base_dir=""))
    key = "cancelled-waiter-regression"
    first_entered = asyncio.Event()
    release_first = asyncio.Event()
    second_started = asyncio.Event()
    third_entered = asyncio.Event()

    async def holder():
        async with _quota_turn(key):
            first_entered.set()
            await release_first.wait()

    async def cancelled_waiter():
        second_started.set()
        async with _quota_turn(key):
            pytest.fail("cancelled waiter must not enter the quota turn")

    async def final_waiter():
        async with _quota_turn(key):
            third_entered.set()

    first = asyncio.create_task(holder())
    await first_entered.wait()
    second = asyncio.create_task(cancelled_waiter())
    await second_started.wait()
    second.cancel()
    with pytest.raises(asyncio.CancelledError):
        await second

    third = asyncio.create_task(final_waiter())
    await asyncio.sleep(0)
    assert third_entered.is_set() is False

    release_first.set()
    await first
    await asyncio.wait_for(third, timeout=1)
    assert third_entered.is_set() is True


@pytest.mark.asyncio
async def test_concurrent_distinct_hold_creates_do_not_exceed_high_cap(
    bucket_mgr,
    monkeypatch,
):
    install_runtime(bucket_mgr)
    monkeypatch.setattr("tools._common._HIGH_IMP_HARD_CAP", 3)
    monkeypatch.setattr("tools._common._HIGH_IMP_SOFT_WARN", 3)

    for i in range(2):
        await bucket_mgr.create(content=f"existing high hold {i}", importance=9)

    await asyncio.gather(*[
        merge_or_create(
            content=f"distinct concurrent hold {i}",
            tags=[],
            importance=9,
            domain=["并发"],
            valence=0.5,
            arousal=0.5,
            raw_merge=True,
            source_tool="hold",
        )
        for i in range(5)
    ])

    assert await count_high_importance() == 3
    created = [
        bucket
        for bucket in await bucket_mgr.list_all(include_archive=False)
        if bucket["content"].startswith("distinct concurrent hold")
    ]
    assert sum(
        int(bucket["metadata"].get("importance") or 0) >= 9
        for bucket in created
    ) == 1


@pytest.mark.asyncio
async def test_concurrent_set_anchor_does_not_exceed_cap(bucket_mgr, monkeypatch):
    install_runtime(bucket_mgr)
    monkeypatch.setattr(bucket_mgr, "ANCHOR_LIMIT", 3)

    for i in range(2):
        await bucket_mgr.create(content=f"已 anchor {i}", tags=[f"anchor{i}"])
    anchored_ids = []
    all_b = await bucket_mgr.list_all(include_archive=False)
    for b in all_b[:2]:
        await bucket_mgr.set_anchor(b["id"], True)
        anchored_ids.append(b["id"])

    candidates = [await bucket_mgr.create(content=f"候选 anchor {i}") for i in range(5)]

    results = await asyncio.gather(*[
        bucket_mgr.set_anchor(bid, True) for bid in candidates
    ])

    final_count = await bucket_mgr.count_anchors()
    assert final_count == 3, f"anchor 配额被冲破：cap=3 实际={final_count}"
    succeeded = [r for r in results if r.get("ok")]
    assert len(succeeded) == 1, f"应该只有 1 个并发 set_anchor 真正成功，实际 {len(succeeded)} 个: {results}"
