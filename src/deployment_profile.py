"""Backward-compatible imports for :mod:`ombrebrain.security.deployment_profile`."""

from ombrebrain.security.deployment_profile import (
    PROFILE_ADVANCED,
    PROFILE_LOCAL,
    PROFILE_PUBLIC,
    build_profile_patch,
    effective_configuration_report,
    normalize_profile,
    normalize_public_https_origin,
    profile_catalog,
    validate_profile_patch,
)

__all__ = [
    "PROFILE_ADVANCED",
    "PROFILE_LOCAL",
    "PROFILE_PUBLIC",
    "build_profile_patch",
    "effective_configuration_report",
    "normalize_profile",
    "normalize_public_https_origin",
    "profile_catalog",
    "validate_profile_patch",
]
