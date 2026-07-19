"""Compatibility import for the packaged media persistence service.

New code should import from :mod:`ombrebrain.storage.media_store`.
"""

from ombrebrain.storage.media_store import MediaPersistenceError, MediaStore

__all__ = ["MediaPersistenceError", "MediaStore"]
