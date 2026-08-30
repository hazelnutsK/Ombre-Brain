"""BM25 raw 分回归 —— **normalized 排序,raw 过门,两者必须分开**。

score() 的 max 归一会把本轮最强的那条拉成 1.0,不管它的绝对强度低到什么程度。
拿归一分去判断「该不该浮」,等于宣布「每轮总有一条足够相关」——但很多轮她根本
没在说任何值得想起的事。真实日志里「呜呜呜不管 打滚」靠一个「打滚」拿到满分
归一值、进而浮出无关旧事,就是这么来的。

这里注入假索引,不依赖 rank_bm25/jieba,任何环境都能跑。
"""
import bm25_index as B


class _FakeArray(list):
    """ndarray 的最小替身:score_pairs 只用到 .max() 和 .size。"""

    def max(self):
        return max(self)

    @property
    def size(self):
        return len(self)


class _FakeIndex:
    def __init__(self, scores):
        self.scores = scores

    def get_scores(self, tokens):
        return _FakeArray(self.scores)


def _index(scores, ids=("strong", "weak", "zero")):
    idx = B.BM25Index()
    idx._index = _FakeIndex(scores)
    idx._ids = list(ids)
    return idx


def test_raw_survives_while_normalized_saturates(monkeypatch):
    """同样的 norm=1.0,raw 可以差几十倍——这正是绝对门要看 raw 的原因。"""
    monkeypatch.setattr(B, "_BM25_AVAILABLE", True)

    strong = _index([8.40, 2.10, 0.0]).score_pairs("酸奶拿铁到底是什么")
    weak = _index([0.31, 0.05, 0.0]).score_pairs("呜呜呜不管 打滚")

    # 两轮的第一名都被归一成满分,看 norm 完全分不出强弱
    assert strong["strong"][0] == 1.0
    assert weak["strong"][0] == 1.0

    # raw 才留住了绝对强度
    assert strong["strong"][1] == 8.40
    assert weak["strong"][1] == 0.31
    assert strong["strong"][1] > weak["strong"][1] * 20


def test_score_stays_backward_compatible(monkeypatch):
    """score() 是老接口,返回值必须跟加 score_pairs 之前逐键相等。"""
    monkeypatch.setattr(B, "_BM25_AVAILABLE", True)
    idx = _index([4.0, 1.0, 0.0])

    assert idx.score("查询") == {
        bid: norm for bid, (norm, _raw) in idx.score_pairs("查询").items()
    }
    # 归一语义没变:最高分 = 1.0,零分不进结果
    assert idx.score("查询") == {"strong": 1.0, "weak": 0.25}


def test_soft_dependency_and_edges(monkeypatch):
    """软依赖缺包 / 无索引 / 空查询 / 全零分,一律安静返回 {},不抛。"""
    monkeypatch.setattr(B, "_BM25_AVAILABLE", True)

    assert _index([0.0, 0.0, 0.0]).score_pairs("x") == {}, "全零分不该有结果"
    assert _index([1.0]).score_pairs("") == {}, "空查询不该有结果"

    no_index = B.BM25Index()
    assert no_index.score_pairs("x") == {}, "索引没建起来时不该抛"

    monkeypatch.setattr(B, "_BM25_AVAILABLE", False)
    assert _index([5.0]).score_pairs("x") == {}, "缺包时必须静默 no-op"
    assert _index([5.0]).score("x") == {}
