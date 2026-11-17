"""Multi-ecosystem source adapters converting partner payloads into canonical AdStream events."""

from adstream.adapters.base import AdapterRegistry, SourceAdapter, build_canonical_event
from adstream.adapters.ecosystems import (
    AmazonAdsAdapter,
    CanonicalPassthroughAdapter,
    GoogleAdsAdapter,
    MetaAdsAdapter,
    ProgrammaticAdapter,
    RetailMediaAdapter,
    YouTubeAdsAdapter,
)

__all__ = [
    "AdapterRegistry",
    "AmazonAdsAdapter",
    "CanonicalPassthroughAdapter",
    "GoogleAdsAdapter",
    "MetaAdsAdapter",
    "ProgrammaticAdapter",
    "RetailMediaAdapter",
    "SourceAdapter",
    "YouTubeAdsAdapter",
    "build_canonical_event",
]
