"""Compatibility import for the packaged ledger replay validator.

New code should import from :mod:`ombrebrain.eventsourcing.ledger_replay`.
"""

from ombrebrain.eventsourcing.ledger_replay import LedgerReplayValidator

__all__ = ["LedgerReplayValidator"]
