"""Compatibility import for packaged provider-detection helpers.

New code should import from :mod:`ombrebrain.integrations.provider_detect`.
"""

from ombrebrain.integrations.provider_detect import (
    endpoint_hostname,
    is_gemini_native_host,
    is_gemini_openai_compat_endpoint,
    is_known_cloud_embedding_endpoint,
    is_siliconflow_endpoint,
    normalize_model_for_endpoint,
    strip_native_resource_prefix,
)

__all__ = [
    "endpoint_hostname",
    "is_gemini_native_host",
    "is_gemini_openai_compat_endpoint",
    "is_known_cloud_embedding_endpoint",
    "is_siliconflow_endpoint",
    "normalize_model_for_endpoint",
    "strip_native_resource_prefix",
]
