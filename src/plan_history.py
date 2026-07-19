"""Compatibility import for the packaged plan-history helpers.

New code should import from :mod:`ombrebrain.domain.plan_history`.
"""

from ombrebrain.domain.plan_history import append_plan_change_log

__all__ = ["append_plan_change_log"]
