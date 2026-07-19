"""Compatibility import for the packaged memory-state wording helpers.

New code should import from :mod:`ombrebrain.domain.memory_messages`.
"""

from ombrebrain.domain.memory_messages import resolved_hint

__all__ = ["resolved_hint"]
