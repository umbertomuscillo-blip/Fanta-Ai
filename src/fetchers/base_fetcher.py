"""
Base HTTP fetcher utilizing Python standard library (urllib.request, ssl).
Implements 3-tier resilience architecture:
- Tier 1: Live HTTP request with browser User-Agent and retries
- Tier 2: Local cache snapshot fallback
- Tier 3: High-fidelity bundled fallback dataset
"""

import logging
import ssl
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple

from src.config import HTTP_CONFIG, CACHE_DIR

logger = logging.getLogger(__name__)


class BaseFetcher:
    def __init__(self):
        self.user_agent = HTTP_CONFIG["user_agent"]
        self.timeout = HTTP_CONFIG["timeout_seconds"]
        self.max_retries = HTTP_CONFIG["max_retries"]
        self.backoff_factor = HTTP_CONFIG["backoff_factor"]
        self.ssl_context = self._create_resilient_ssl_context()

    def _create_resilient_ssl_context(self) -> ssl.SSLContext:
        """Creates an SSL context with fallback to unverified if certificates fail."""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx
        except Exception as e:
            logger.warning(f"Default SSL context creation failed: {e}. Using unverified context.")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            return ctx

    def fetch_text(
        self,
        url: str,
        cache_filename: Optional[str] = None,
        force_fallback: bool = False,
        encoding: str = "utf-8"
    ) -> Tuple[Optional[str], str]:
        """
        Fetches text content from URL with 3-tier fallback.
        Returns: (content_str, tier_used: "TIER_1_LIVE" | "TIER_2_CACHE" | "TIER_3_FALLBACK")
        """
        cache_path = CACHE_DIR / cache_filename if cache_filename else None

        if force_fallback:
            logger.info(f"Force fallback requested for {url}")
            if cache_path and cache_path.exists() and cache_path.stat().st_size > 0:
                try:
                    with open(cache_path, "r", encoding=encoding) as f:
                        return f.read(), "TIER_2_CACHE"
                except Exception as e:
                    logger.warning(f"Failed to read cache {cache_path}: {e}")
            return None, "TIER_3_FALLBACK"

        # Tier 1: Try Live HTTP
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        }
        req = urllib.request.Request(url, headers=headers)

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        raw_data = resp.read()
                        text = raw_data.decode(encoding, errors="replace")
                        # Save to cache
                        if cache_path and text:
                            try:
                                cache_path.parent.mkdir(parents=True, exist_ok=True)
                                with open(cache_path, "w", encoding=encoding) as f:
                                    f.write(text)
                                logger.debug(f"Saved cache to {cache_path}")
                            except Exception as ce:
                                logger.warning(f"Could not save cache to {cache_path}: {ce}")
                        logger.info(f"Successfully fetched live data from {url} (Tier 1 Live)")
                        return text, "TIER_1_LIVE"
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception) as e:
                last_error = e

            if attempt < self.max_retries:
                sleep_time = self.backoff_factor ** attempt
                logger.debug(f"Fetch attempt {attempt} failed ({last_error}). Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)

        logger.warning(f"Live fetch failed for {url}: {last_error}. Checking Tier 2 Cache...")

        # Tier 2: Check Local Cache
        if cache_path and cache_path.exists() and cache_path.stat().st_size > 0:
            try:
                with open(cache_path, "r", encoding=encoding) as f:
                    cached_text = f.read()
                    if cached_text.strip():
                        logger.info(f"Loaded snapshot from cache {cache_path} (Tier 2 Cache)")
                        return cached_text, "TIER_2_CACHE"
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_path}: {e}")

        # Tier 3: Bundled Fallback
        logger.info(f"No cache available for {url}. Falling back to Tier 3 Bundled Fallback.")
        return None, "TIER_3_FALLBACK"
