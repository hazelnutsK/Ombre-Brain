"""Compatibility import for packaged ledger replay property checks.

New code should import from :mod:`ombrebrain.eventsourcing.ledger_property`.
"""

from ombrebrain.eventsourcing.ledger_property import LedgerReplayPropertyRunner

__all__ = ["LedgerReplayPropertyRunner"]
