"""Compatibility import for the packaged trace catalog projection.

New code should import from :mod:`ombrebrain.projection.projection_mirror`.
"""

from ombrebrain.projection.projection_mirror import TraceCatalogProjection

__all__ = ["TraceCatalogProjection"]
