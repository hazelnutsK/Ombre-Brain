"""Compatibility import for the packaged vector projection manifest.

New code should import from :mod:`ombrebrain.projection.projection_vector`.
"""

from ombrebrain.projection.projection_vector import TraceVectorProjectionManifest

__all__ = ["TraceVectorProjectionManifest"]
