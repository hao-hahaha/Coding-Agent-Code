# SPDX-License-Identifier: Apache-2.0
"""
Unified headline fetcher (NewsAPI → RSS → cached local file).

Used by MacroSentinel & any RAG pipeline that needs fresh news.
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import time
from typing import List

_LOG = logging.getLogger("alpha_factory.news")
_LOG.addHandler(logging.NullHandler())

_CACHE = pathlib.Path("/tmp/alpha_factory_news_cache.json")
_NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

try:
    from newsapi import NewsApiClient  # type: ignore
    _NEWSAPI_OK = True
except ModuleNotFoundError:
    _NEWSAPI_OK = False

try:
    import feedparser  # type: ignore
    _FEED_OK = True
except ModuleNotFoundError:
    _FEED_OK = False


def latest_headlines(limit: int = 20) -> List[str]:
    """Return at most *limit* recent headlines (newest first)."""
    if _NEWSAPI_OK and _NEWSAPI_KEY:
        return _newsapi_headlines(limit)

    if _FEED_OK:
        return _rss_headlines(limit)

    _LOG.warning("No news source available – serving cached headlines only")
    return _cached_headlines(limit)


# --------------------------------------------------------------------- #
#  Internal sources                                                     #
# --------------------------------------------------------------------- #
def _newsapi_headlines(limit: int) -> List[str]:
    client = NewsApiClient(api_key=_NEWSAPI_KEY)
    res = client.get_top_headlines(language="en", page_size=limit)
    heads = [a["title"] for a in res.get("articles", [])]
    _save_cache(heads)
    return heads


def _rss_headlines(limit: int) -> List[str]:
    feeds = (
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
    )
    entries = []
    for url in feeds:
        entries.extend(feedparser.parse(url).entries)  # type: ignore[attr-defined]
    heads = [e.title for e in sorted(entries, key=lambda e: e.published_parsed, reverse=True)][:limit]
    _save_cache(heads)
    return heads


# --------------------------------------------------------------------- #
#  Cache helpers                                                        #
# --------------------------------------------------------------------- #
def _save_cache(headlines: List[str]) -> None:
    _CACHE.write_text(json.dumps({"t": time.time(), "h": headlines}))


def _cached_headlines(limit: int) -> List[str]:
    if _CACHE.exists():
        try:
            data = json.loads(_CACHE.read_text())
            return data["h"][:limit]
        except (json.JSONDecodeError, OSError):
            pass
    return ["(no headlines available – offline)"]
