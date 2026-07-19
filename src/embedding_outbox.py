"""Compatibility import for the packaged embedding outbox service.

New code should import from :mod:`ombrebrain.storage.embedding_outbox`.
"""

from ombrebrain.storage.embedding_outbox import EmbeddingOutbox, content_hash

__all__ = ["EmbeddingOutbox", "content_hash"]
