"""
Fetcher for Fantacalcio 2026/2027 Probabili Formazioni (Lineups & Ballotaggi).
"""

import logging
from typing import Tuple, Optional
from src.config import SOURCES
from src.fetchers.base_fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class LineupsFetcher(BaseFetcher):
    def fetch_lineups(
        self, force_fallback: bool = False
    ) -> Tuple[Optional[str], str]:
        """
        Retrieves raw HTML for Probabili Formazioni.
        Returns (lineups_html, tier_used)
        """
        logger.info("Ingesting probabili formazioni from fantacalcio.it...")
        return self.fetch_text(
            SOURCES["probabili_formazioni"],
            cache_filename="lineups_raw.html",
            force_fallback=force_fallback
        )
