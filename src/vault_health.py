"""Compatibility import for the packaged vault integrity inspector.

New code should import from :mod:`ombrebrain.storage.vault_health`.
"""

from ombrebrain.storage.vault_health import inspect_vault

__all__ = ["inspect_vault"]
