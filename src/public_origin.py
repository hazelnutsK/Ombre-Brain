"""Compatibility import for packaged public-origin security helpers.

New code should import from :mod:`ombrebrain.security.public_origin`.
"""

from ombrebrain.security.public_origin import (
    MAX_PUBLIC_URI_CHARS,
    configured_public_origin,
    normalize_http_resource,
    normalize_public_origin,
)

__all__ = [
    "MAX_PUBLIC_URI_CHARS",
    "configured_public_origin",
    "normalize_http_resource",
    "normalize_public_origin",
]
