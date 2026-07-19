"""Compatibility import for the packaged SQLite trace projection.

New code should import from :mod:`ombrebrain.projection.projection_sqlite`.
"""

from ombrebrain.projection.projection_sqlite import TraceSQLiteProjection

__all__ = ["TraceSQLiteProjection"]
