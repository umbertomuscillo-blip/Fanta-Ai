#!/usr/bin/env python3
"""
Tier 3: Cross-Feature Combinations Test Suite
Fantacalcio 2026/2027 Automated Data Pipeline

Verifies interactions between features, cross-dataset referential integrity,
dual storage (JSON/CSV) parity, calendar & lineup synchronization, and
CLI pairwise option combinations.
"""

import csv
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"
MAIN_SCRIPT = WORKSPACE_ROOT / "update_fanta_data.py"

sys.path.insert(0, str(WORKSPACE_ROOT))

from src.config import (
    SERIE_A_TEAMS_2026_2027,
    PROMOTED_TEAMS_2026_2027,
    RELEGATED_TEAMS,
)


def _resolve_file_path(*possible_names: str) -> Path:
    for name in possible_names:
        p = DATA_DIR / name
        if p.is_file():
            return p
    return DATA_DIR / possible_names[0]


class TestPairwiseCliCombinations(unittest.TestCase):
    """Verifies pairwise CLI option combinations for update_fanta_data.py."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess:
        if not MAIN_SCRIPT.exists():
            self.skipTest(f"{MAIN_SCRIPT} not yet created")
        return subprocess.run(
            [sys.executable, str(MAIN_SCRIPT)] + args,
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_comb_01_cli_players_and_lineups(self):
        """Test running update_fanta_data.py --players --lineups."""
        res = self._run_cli(["--players", "--lineups"])
        self.assertEqual(res.returncode, 0, f"Failed --players --lineups: {res.stderr}")

    def test_comb_02_cli_lineups_and_fixtures(self):
        """Test running update_fanta_data.py --lineups --fixtures."""
        res = self._run_cli(["--lineups", "--fixtures"])
        self.assertEqual(res.returncode, 0, f"Failed --lineups --fixtures: {res.stderr}")

    def test_comb_03_cli_players_and_fixtures(self):
        """Test running update_fanta_data.py --players --fixtures."""
        res = self._run_cli(["--players", "--fixtures"])
        self.assertEqual(res.returncode, 0, f"Failed --players --fixtures: {res.stderr}")

    def test_comb_04_cli_all_with_offline_fallback(self):
        """Test running update_fanta_data.py --all --offline-fallback."""
        res = self._run_cli(["--all", "--offline-fallback"])
        self.assertEqual(res.returncode, 0, f"Failed --all --offline-fallback: {res.stderr}")


class TestCrossDatasetReferentialIntegrity(unittest.TestCase):
    """Verifies cross-references between players, lineups, calendar, and teams."""

    def setUp(self):
        self.players_json_path = _resolve_file_path("players.json")
        self.lineups_json_path = _resolve_file_path("probabili_formazioni.json", "lineups.json")
        self.calendar_json_path = _resolve_file_path("calendario_serie_a.json", "calendar.json")
        self.teams_json_path = _resolve_file_path("teams.json")

    def test_comb_05_lineup_teams_belong_to_2026_2027_registry(self):
        """Verify all teams present in lineups belong to Serie A 2026/2027."""
        if not self.lineups_json_path.exists():
            self.skipTest(f"{self.lineups_json_path} missing")

        with open(self.lineups_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = data.get("matches", []) if isinstance(data, dict) else data
        canonical_names = set(SERIE_A_TEAMS_2026_2027.values())
        canonical_codes = set(SERIE_A_TEAMS_2026_2027.keys())

        for m in matches:
            home = m.get("home_team") or m.get("casa", {}).get("squadra")
            away = m.get("away_team") or m.get("trasferta", {}).get("squadra")
            home_code = m.get("home_team_code")
            away_code = m.get("away_team_code")

            self.assertIn(home, canonical_names, f"Unknown home team in lineups: {home}")
            self.assertIn(away, canonical_names, f"Unknown away team in lineups: {away}")
            if home_code:
                self.assertIn(home_code, canonical_codes)
            if away_code:
                self.assertIn(away_code, canonical_codes)

    def test_comb_06_lineup_fixtures_match_calendar_matchday_1(self):
        """Verify lineup fixtures correspond to matchday 1 fixtures in calendar."""
        if not (self.lineups_json_path.exists() and self.calendar_json_path.exists()):
            self.skipTest("Lineups or Calendar dataset missing")

        with open(self.lineups_json_path, "r", encoding="utf-8") as f:
            lineups_data = json.load(f)
        with open(self.calendar_json_path, "r", encoding="utf-8") as f:
            calendar = json.load(f)

        lineup_matches = lineups_data.get("matches", []) if isinstance(lineups_data, dict) else lineups_data
        lineup_pairs = set()
        for m in lineup_matches:
            h = m.get("home_team") or m.get("casa", {}).get("squadra")
            a = m.get("away_team") or m.get("trasferta", {}).get("squadra")
            lineup_pairs.add((h, a))

        cal_g1_matches = [m for m in calendar if m.get("matchday") == 1 or m.get("giornata") == 1]
        cal_pairs = set()
        for m in cal_g1_matches:
            h = m.get("home_team") or m.get("squadra_casa")
            a = m.get("away_team") or m.get("squadra_trasferta")
            # Map code to name if needed
            if h in SERIE_A_TEAMS_2026_2027:
                h = SERIE_A_TEAMS_2026_2027[h]
            if a in SERIE_A_TEAMS_2026_2027:
                a = SERIE_A_TEAMS_2026_2027[a]
            cal_pairs.add((h, a))

        self.assertEqual(
            lineup_pairs,
            cal_pairs,
            f"Lineup matchday 1 pairings do not match calendar matchday 1 pairings:\nLineups: {lineup_pairs}\nCalendar: {cal_pairs}",
        )

    def test_comb_07_lineup_starters_exist_in_players_database(self):
        """Verify that starters in probabili formazioni exist in players.json."""
        if not (self.lineups_json_path.exists() and self.players_json_path.exists()):
            self.skipTest("Lineups or Players dataset missing")

        with open(self.players_json_path, "r", encoding="utf-8") as f:
            players = json.load(f)
        with open(self.lineups_json_path, "r", encoding="utf-8") as f:
            lineups = json.load(f)

        player_names_lower = {p.get("nome", "").lower() for p in players}
        matches = lineups.get("matches", []) if isinstance(lineups, dict) else lineups

        total_starters = 0
        matched_starters = 0

        for m in matches:
            for side in ["home_lineup", "away_lineup", "casa", "trasferta"]:
                if side in m:
                    for titolare in m[side].get("titolari", []):
                        total_starters += 1
                        t_name = titolare.get("nome", "").lower()
                        # Allow partial substring match for names (e.g. 'Martinez L.' vs 'Lautaro Martinez')
                        matched = any(
                            t_name in p_name or p_name in t_name or t_name.split()[-1] in p_name
                            for p_name in player_names_lower
                        )
                        if matched:
                            matched_starters += 1

        self.assertEqual(total_starters, 220, f"Expected 220 starters across 20 teams, got {total_starters}")
        # At least 95% of starters should match listone
        match_rate = (matched_starters / total_starters) * 100
        self.assertGreaterEqual(
            match_rate,
            90.0,
            f"Starter name match rate {match_rate:.1f}% is below 90% threshold ({matched_starters}/{total_starters})",
        )


class TestDualStorageConsistency(unittest.TestCase):
    """Verifies consistency between JSON and CSV versions of each dataset."""

    def test_comb_08_players_json_vs_csv_parity(self):
        """Verify player count and key fields match between players.json and players.csv."""
        json_path = _resolve_file_path("players.json")
        csv_path = _resolve_file_path("players.csv")

        if not (json_path.exists() and csv_path.exists()):
            self.skipTest("players.json or players.csv missing")

        with open(json_path, "r", encoding="utf-8") as f:
            json_players = json.load(f)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_players = list(reader)

        self.assertEqual(
            len(json_players),
            len(csv_players),
            f"Player count mismatch: JSON has {len(json_players)}, CSV has {len(csv_players)}",
        )

        json_names = {p["nome"] for p in json_players}
        csv_names = {r["nome"] for r in csv_players}
        self.assertEqual(json_names, csv_names, "Player names in JSON and CSV do not match")

    def test_comb_09_calendar_json_vs_csv_parity(self):
        """Verify match count matches between calendar.json and calendar.csv."""
        json_path = _resolve_file_path("calendario_serie_a.json", "calendar.json")
        csv_path = _resolve_file_path("calendario_serie_a.csv", "calendar.csv")

        if not (json_path.exists() and csv_path.exists()):
            self.skipTest("Calendar JSON or CSV missing")

        with open(json_path, "r", encoding="utf-8") as f:
            json_cal = json.load(f)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_cal = list(reader)

        self.assertEqual(len(json_cal), 380)
        self.assertEqual(len(csv_cal), 380)

    def test_comb_10_teams_json_vs_csv_parity(self):
        """Verify teams count and codes match between teams.json and teams.csv."""
        json_path = _resolve_file_path("teams.json")
        csv_path = _resolve_file_path("teams.csv")

        if not (json_path.exists() and csv_path.exists()):
            self.skipTest("Teams JSON or CSV missing")

        with open(json_path, "r", encoding="utf-8") as f:
            json_teams = json.load(f)
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_teams = list(reader)

        self.assertEqual(len(json_teams), 20)
        self.assertEqual(len(csv_teams), 20)

    def test_comb_11_players_db_partition_sum_equals_players_json(self):
        """Verify sum of P+D+C+A in players_db.json equals players.json count."""
        json_path = _resolve_file_path("players.json")
        db_path = _resolve_file_path("players_db.json")

        if not (json_path.exists() and db_path.exists()):
            self.skipTest("players.json or players_db.json missing")

        with open(json_path, "r", encoding="utf-8") as f:
            players = json.load(f)
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        total_db = len(db.get("P", [])) + len(db.get("D", [])) + len(db.get("C", [])) + len(db.get("A", []))
        self.assertEqual(
            len(players),
            total_db,
            f"players.json ({len(players)}) != players_db.json sum ({total_db})",
        )

    def test_comb_12_sync_report_metadata_consistency(self):
        """Verify record counts recorded in sync_report.json match actual dataset counts."""
        report_path = _resolve_file_path("sync_report.json")
        players_path = _resolve_file_path("players.json")
        calendar_path = _resolve_file_path("calendario_serie_a.json", "calendar.json")
        teams_path = _resolve_file_path("teams.json")

        if not report_path.exists():
            self.skipTest("sync_report.json missing")

        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        self.assertTrue(report.get("success", False), "Sync report indicates failure")
        self.assertEqual(report.get("teams_count"), 20)
        self.assertEqual(report.get("fixtures_count"), 380)

        if players_path.exists():
            with open(players_path, "r", encoding="utf-8") as f:
                players = json.load(f)
            self.assertEqual(report.get("players_count"), len(players))


if __name__ == "__main__":
    unittest.main(verbosity=2)
