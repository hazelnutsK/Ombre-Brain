"""search() 要在每条命中上挂 score_parts —— 分车道的原始证据。

为什么需要它:score 是 7 维加权归一后的**排序分**,其中 emotion/time/
importance/touch 跟「这条记忆和当前这句话相不相关」毫无关系,却占了 41~58%
的权重;再叠加 fuzzy_threshold=50 的准入门,实测分布挤在 50~65 的窄带里。
在这样一个分数上切阈值等于切噪声,所以「该不该浮」只能看各车道的绝对值。

配套:bm25 的 raw 与 normalized 分离见 test_bm25_raw_scores.py。
"""
import pytest


@pytest.mark.asyncio
async def test_score_parts_carries_per_lane_evidence(bucket_mgr):
    await bucket_mgr.create(
        content="今天确认喝的是真拿铁，不会再把酸奶倒进咖啡",
        name="酸奶拿铁", domain=["日常"],
    )
    results = await bucket_mgr.search("酸奶拿铁")
    assert results, "字面命中的查询必须能召回"

    parts = results[0].get("score_parts")
    assert parts is not None, "每条命中都要带上分车道证据"

    # 与查询相关的车道
    for lane in ("topic", "bm25_norm", "bm25_raw", "literal", "semantic"):
        assert lane in parts, f"缺了 {lane} 车道"
    # 与查询无关、只反映记忆自身属性的维度(50 分地板的来源),也要留证据
    for lane in ("emotion", "time", "importance", "touch"):
        assert lane in parts, f"缺了 {lane} 车道"

    assert isinstance(parts["literal"], bool)
    assert parts["bm25_raw"] >= 0.0
    assert 0.0 <= parts["topic"] <= 1.0


@pytest.mark.asyncio
async def test_score_parts_does_not_disturb_ranking(bucket_mgr):
    """纯增量:加 score_parts 不能改变原有的排序与 score 取值。"""
    await bucket_mgr.create(content="她喜欢秋天的傍晚和凉风", name="秋天")
    await bucket_mgr.create(content="关于向量检索和关键词匹配", name="检索")

    results = await bucket_mgr.search("秋天")
    assert results
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), "仍按 score 倒序"
    for r in results:
        assert 0 <= r["score"] <= 100


@pytest.mark.asyncio
async def test_timings_out_param_is_optional(bucket_mgr):
    """timings 是可选 out-param:不传照常工作,传了就填分段耗时。"""
    await bucket_mgr.create(content="用来触发一次检索的记忆", name="随便")

    assert await bucket_mgr.search("随便") is not None, "不传 timings 不能出错"

    timings: dict = {}
    await bucket_mgr.search("随便", timings=timings)
    for stage in ("list_all_ms", "bm25_ms", "rank_ms"):
        assert stage in timings, f"缺了 {stage} 埋点"
        assert isinstance(timings[stage], int) and timings[stage] >= 0
    assert timings["candidates"] >= timings["scored"], "候选数不可能少于打分数"
