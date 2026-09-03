"""
Fetcher for Serie A 2026/2027 Calendar and Fixtures.
"""

import logging
from typing import Tuple, Optional
from src.config import SOURCES
from src.fetchers.base_fetcher import BaseFetcher

logger = logging.getLogger(__name__)


class FixturesFetcher(BaseFetcher):
    def fetch_fixtures(
        self, force_fallback: bool = False
    ) -> Tuple[Optional[str], str]:
        """
        Retrieves raw fixtures text from OpenFootball repository.
        Returns (fixtures_text, tier_used)
        """
        logger.info("Ingesting Serie A 2026/2027 calendar from OpenFootball...")
        return self.fetch_text(
            SOURCES["calendario_openfootball"],
            cache_filename="fixtures_raw.txt",
            force_fallback=force_fallback
        )
