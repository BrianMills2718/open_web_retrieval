"""open_web_retrieval package exports."""

from open_web_retrieval._version import __version__

from open_web_retrieval.async_client import AsyncOpenWebRetrievalClient
from open_web_retrieval.async_fetch import AsyncSourceFetcher
from open_web_retrieval.cache import CacheStats, DiskCache
from open_web_retrieval.client import OpenWebRetrievalClient, SourceRecordBatch
from open_web_retrieval.models import (
    ExtractedDocument,
    FetchRequest,
    FetchedResource,
    SearchHit,
    SearchQuery,
    SourceRecord,
)
from open_web_retrieval.exceptions import (
    CapabilityNotSupportedError,
    FetchError,
    OpenWebRetrievalError,
    ProviderUnavailableError,
    RenderError,
    RetrievalError,
)
from open_web_retrieval.fetch_extract import SourceFetcher
from open_web_retrieval.models import FetchMetrics
from open_web_retrieval.medium import (
    MediumArticle,
    MediumFeedItem,
    fetch_medium_article,
    parse_medium_feed,
    search_medium_query,
)

__all__ = [
    "AsyncOpenWebRetrievalClient",
    "AsyncSourceFetcher",
    "CacheStats",
    "DiskCache",
    "CapabilityNotSupportedError",
    "ExtractedDocument",
    "FetchRequest",
    "FetchedResource",
    "MediumArticle",
    "MediumFeedItem",
    "OpenWebRetrievalClient",
    "OpenWebRetrievalError",
    "ProviderUnavailableError",
    "FetchError",
    "FetchMetrics",
    "RenderError",
    "RetrievalError",
    "SourceFetcher",
    "SearchHit",
    "SearchQuery",
    "SourceRecord",
    "SourceRecordBatch",
    "fetch_medium_article",
    "parse_medium_feed",
    "search_medium_query",
    "__version__",
]

# Auto-register @tool decorated functions
try:
    from open_web_retrieval.adapters.tools import (  # noqa: F401
        brave_search, searxng_search, tavily_search, exa_search,
        medium_search, medium_get_article, medium_feed,
    )
except ImportError:
    pass  # llm_client not installed
