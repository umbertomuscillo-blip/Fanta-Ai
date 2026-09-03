"""
Data Pipeline Coordinator for Fantacalcio 2026/2027.
Orchestrates Fetching -> Parsing -> Validation -> Exporting -> Sync Reporting.
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional, List

from src.config import DATA_DIR
from src.fetchers import PlayersFetcher, LineupsFetcher, FixturesFetcher
from src.parsers import PlayersParser, LineupsParser, FixturesParser
from src.storage import JsonExporter, CsvExporter
from src.validators import SeasonValidator
from src.models import SyncReport, Player, MatchLineup, MatchFixture

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self, force_fallback: bool = False, verbose: bool = False):
        self.force_fallback = force_fallback
        self.verbose = verbose
        self.players_fetcher = PlayersFetcher()
        self.lineups_fetcher = LineupsFetcher()
        self.fixtures_fetcher = FixturesFetcher()

        self.players_parser = PlayersParser()
        self.lineups_parser = LineupsParser()
        self.fixtures_parser = FixturesParser()

        self.validator = SeasonValidator()
        self.json_exporter = JsonExporter()
        self.csv_exporter = CsvExporter()

    def run(
        self,
        fetch_players: bool = True,
        fetch_lineups: bool = True,
        fetch_fixtures: bool = True
    ) -> SyncReport:
        """
        Executes complete pipeline run and exports datasets to data/
        """
        start_time = time.time()
        logger.info(f"Starting Fantacalcio 2026/2027 pipeline (force_fallback={self.force_fallback})...")

        source_tiers = {}
        errors = []

        players: Optional[List[Player]] = None
        lineups: Optional[List[MatchLineup]] = None
        fixtures: Optional[List[MatchFixture]] = None

        # 1. Fetch & Parse Players
        if fetch_players:
            try:
                q_html, s_html, tier = self.players_fetcher.fetch_quotazioni_and_stats(
                    force_fallback=self.force_fallback
                )
                source_tiers["players"] = tier
                players = self.players_parser.parse(q_html, s_html)
            except Exception as e:
                msg = f"Players pipeline stage failed: {e}"
                logger.error(msg)
                errors.append(msg)
                players = self.players_parser.parse(None, None)
                source_tiers["players"] = "TIER_3_FALLBACK"
        else:
            # Load existing players if available
            players = self.players_parser.parse(None, None)
            source_tiers["players"] = "PRESERVED_EXISTING"

        # 2. Fetch & Parse Lineups
        if fetch_lineups:
            try:
                l_html, tier = self.lineups_fetcher.fetch_lineups(
                    force_fallback=self.force_fallback
                )
                source_tiers["lineups"] = tier
                lineups = self.lineups_parser.parse(l_html)
            except Exception as e:
                msg = f"Lineups pipeline stage failed: {e}"
                logger.error(msg)
                errors.append(msg)
                lineups = self.lineups_parser.parse(None)
                source_tiers["lineups"] = "TIER_3_FALLBACK"
        else:
            # Load existing lineups if available
            lineups = self.lineups_parser.parse(None)
            source_tiers["lineups"] = "PRESERVED_EXISTING"

        # 3. Fetch & Parse Fixtures
        if fetch_fixtures:
            try:
                f_txt, tier = self.fixtures_fetcher.fetch_fixtures(
                    force_fallback=self.force_fallback
                )
                source_tiers["fixtures"] = tier
                fixtures = self.fixtures_parser.parse(f_txt)
            except Exception as e:
                msg = f"Fixtures pipeline stage failed: {e}"
                logger.error(msg)
                errors.append(msg)
                fixtures = self.fixtures_parser.parse(None)
                source_tiers["fixtures"] = "TIER_3_FALLBACK"
        else:
            # Load existing fixtures if available
            fixtures = self.fixtures_parser.parse(None)
            source_tiers["fixtures"] = "PRESERVED_EXISTING"

        # 4. Validation
        if players and lineups and fixtures:
            try:
                self.validator.validate_all(players, lineups, fixtures)
            except Exception as e:
                msg = f"Validation failed: {e}"
                logger.error(msg)
                errors.append(msg)

        # 5. Export JSON & CSV
        self.json_exporter.export_all(
            players=players if fetch_players else players,
            lineups=lineups if fetch_lineups else lineups,
            fixtures=fixtures if fetch_fixtures else fixtures
        )
        self.csv_exporter.export_all(
            players=players if fetch_players else players,
            lineups=lineups if fetch_lineups else lineups,
            fixtures=fixtures if fetch_fixtures else fixtures
        )

        exec_duration = round(time.time() - start_time, 3)
        success = len(errors) == 0

        # 6. Generate & Export SyncReport
        report = SyncReport(
            timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            success=success,
            players_count=len(players) if players else 0,
            lineups_count=len(lineups) if lineups else 0,
            fixtures_count=len(fixtures) if fixtures else 0,
            teams_count=20,
            execution_time_sec=exec_duration,
            errors=errors,
            source_tiers=source_tiers
        )

        self.json_exporter.export_sync_report(report)
        logger.info(f"Pipeline finished in {exec_duration}s. Success={success}")
        return report


def run_pipeline(
    fetch_players: bool = True,
    fetch_lineups: bool = True,
    fetch_fixtures: bool = True,
    force_fallback: bool = False,
    verbose: bool = False
) -> SyncReport:
    """Convenience helper function."""
    pipeline = DataPipeline(force_fallback=force_fallback, verbose=verbose)
    return pipeline.run(
        fetch_players=fetch_players,
        fetch_lineups=fetch_lineups,
        fetch_fixtures=fetch_fixtures
    )
