"""trace_id 由调用方生成、服务端复用 —— 以及它进日志前必须被清洗。

为什么方向是「调用方生成」:relay 的预算是 2s,这里是 8s。relay 超时那几轮
根本收不到响应,如果 id 是服务端生成、随响应返回的,恰好在唯一需要对账的场景
(「relay 放弃了,服务端到底跑了多久」)拿不到 id。所以 id 必须先在调用方手里。

清洗是因为这个值会原样进 logger 行:带换行的 trace_id 能在日志里伪造整行。
"""
from web.hooks import _sanitize_trace_id


def test_keeps_normal_ids():
    assert _sanitize_trace_id("d2637a95") == "d2637a95"
    assert _sanitize_trace_id("trace-2026_08-31") == "trace-2026_08-31"


def test_strips_log_injection():
    # 换行是重点:不过滤的话日志里能凭空多出一行伪造记录
    assert "\n" not in _sanitize_trace_id("abc\n[recall] trace=fake cards=999")
    assert _sanitize_trace_id("abc\ndef") == "abcdef"
    assert _sanitize_trace_id("a b\tc") == "abc"
    assert _sanitize_trace_id("../../etc/passwd") == "etcpasswd"


def test_truncates_and_handles_empty():
    assert len(_sanitize_trace_id("x" * 500)) == 32
    # 空 / None / 清洗后为空 —— 都返回空串,让调用处回退到自己生成的 id
    assert _sanitize_trace_id("") == ""
    assert _sanitize_trace_id(None) == ""
    assert _sanitize_trace_id("!!!") == ""
