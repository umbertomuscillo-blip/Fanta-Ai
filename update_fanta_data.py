#!/usr/bin/env python3
"""
Fantacalcio 2026/2027 Data Pipeline Master CLI.
Executes automated ingestion, parsing, validation, and persistence of
players, lineups, fixtures, and teams data.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.pipeline import DataPipeline


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%H:%M:%S"
    logging.basicConfig(level=level, format=fmt, datefmt=datefmt)


def print_banner():
    print("=" * 70)
    print(" ⚽  FANTACALCIO 2026/2027 AUTOMATED DATA PIPELINE")
    print("=" * 70)


def print_summary_table(report):
    print("\n" + "=" * 70)
    print(" 📊  PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    status_str = "SUCCESS (OK)" if report.success else "COMPLETED WITH WARNINGS"
    print(f" Status:                {status_str}")
    print(f" Execution Time:        {report.execution_time_sec} seconds")
    print(f" Timestamp (UTC):       {report.timestamp}")
    print("-" * 70)
    print(f" Serie A 2026/27 Teams: {report.teams_count} (Como, Parma, Venezia included)")
    print(f" Active Players:        {report.players_count} players (Quotazioni, Stats, Tiers)")
    print(f" Matchday Lineups:      {report.lineups_count} fixtures (20 teams, 11 starters each)")
    print(f" Season Calendar:       {report.fixtures_count} matches (38 matchdays)")
    print("-" * 70)
    print(" Ingestion Source Tiers:")
    for domain, tier in report.source_tiers.items():
        print(f"   • {domain.capitalize():<12}: {tier}")
    if report.errors:
        print("-" * 70)
        print(" Logged Errors:")
        for err in report.errors:
            print(f"   ✖ {err}")
    print("=" * 70)
    print(" Output Files Updated in data/:")
    print("   • data/players.json, data/players.csv, data/players_db.json")
    print("   • data/probabili_formazioni.json, data/probabili_formazioni.csv")
    print("   • data/calendario_serie_a.json, data/calendario_serie_a.csv")
    print("   • data/teams.json, data/teams.csv, data/sync_report.json")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Fantacalcio 2026/2027 Automated Data Pipeline"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all datasets (players, lineups, calendar, teams) [Default]"
    )
    parser.add_argument(
        "--players",
        action="store_true",
        help="Update players, quotazioni, and statistics"
    )
    parser.add_argument(
        "--lineups",
        action="store_true",
        help="Update probable lineups and ballotaggi"
    )
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Update Serie A 2026/2027 calendar and results"
    )
    parser.add_argument(
        "--offline-fallback",
        "--offline",
        action="store_true",
        help="Force use of local cache and bundled fallback dataset without live HTTP"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging"
    )

    args = parser.parse_args()
    setup_logging(args.verbose)
    print_banner()

    # Determine which components to fetch
    has_specific = args.players or args.lineups or args.fixtures
    fetch_players = args.players or not has_specific or args.all
    fetch_lineups = args.lineups or not has_specific or args.all
    fetch_fixtures = args.fixtures or not has_specific or args.all

    try:
        pipeline = DataPipeline(
            force_fallback=args.offline_fallback,
            verbose=args.verbose
        )
        report = pipeline.run(
            fetch_players=fetch_players,
            fetch_lineups=fetch_lineups,
            fetch_fixtures=fetch_fixtures
        )
        print_summary_table(report)
        sys.exit(0)
    except Exception as e:
        logging.exception(f"Fatal error during pipeline execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
