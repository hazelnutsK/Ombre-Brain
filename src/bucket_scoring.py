"""Compatibility import for packaged bucket-scoring helpers.

New code should import from :mod:`ombrebrain.retrieval.bucket_scoring`.
"""

from ombrebrain.retrieval.bucket_scoring import (
    EMOTION_MAX_DIST,
    TIME_DECAY_LAMBDA,
    TIME_FALLBACK_DAYS,
    TOPIC_BODY_SLICE,
    TOPIC_DOMAIN_W,
    TOPIC_NAME_W,
    TOPIC_TAG_W,
    TOUCH_NORMALIZE_CAP,
    calc_emotion_score,
    calc_time_score,
    calc_topic_score,
    calc_touch_score,
)

__all__ = [
    "EMOTION_MAX_DIST",
    "TIME_DECAY_LAMBDA",
    "TIME_FALLBACK_DAYS",
    "TOPIC_BODY_SLICE",
    "TOPIC_DOMAIN_W",
    "TOPIC_NAME_W",
    "TOPIC_TAG_W",
    "TOUCH_NORMALIZE_CAP",
    "calc_emotion_score",
    "calc_time_score",
    "calc_topic_score",
    "calc_touch_score",
]
