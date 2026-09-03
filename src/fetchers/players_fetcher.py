"""
Fetcher for Fantacalcio 2026/2027 Players, Quotazioni and Statistics.
"""

import logging
from typing import Tuple, Optional
from src.config import SOURCES
from src.fetchers.base_fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class PlayersFetcher(BaseFetcher):
    def fetch_quotazioni_and_stats(
        self, force_fallback: bool = False
    ) -> Tuple[Optional[str], Optional[str], str]:
        """
        Retrieves raw HTML for Quotazioni and Statistiche.
        Returns (quotazioni_html, stats_html, tier_used)
        """
        logger.info("Ingesting players quotazioni and statistics...")
        q_text, q_tier = self.fetch_text(
            SOURCES["quotazioni"],
            cache_filename="quotazioni_raw.html",
            force_fallback=force_fallback
        )

        s_text, s_tier = self.fetch_text(
            SOURCES["statistiche"],
            cache_filename="statistiche_raw.html",
            force_fallback=force_fallback
        )

        tier_used = q_tier if q_tier == s_tier else f"{q_tier}/{s_tier}"
        return q_text, s_text, tier_used
