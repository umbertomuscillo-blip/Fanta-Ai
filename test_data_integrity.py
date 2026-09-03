#!/usr/bin/env python3
"""
Acceptance Test Suite: test_data_integrity.py
Fantacalcio 2026/2027 Automated Data Pipeline

Verifies end-to-end data integrity, file existence, strict Serie A 2026/2027
club roster invariants, player role distributions & pricing, 10-match probable
lineups structure, and 38-giornata / 380-match calendar completeness.
"""

import csv
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

# Workspace paths
WORKSPACE_ROOT = Path(__file__).resolve().parent
DATA_DIR = WORKSPACE_ROOT / "data"
MAIN_SCRIPT = WORKSPACE_ROOT / "update_fanta_data.py"

# Authoritative Serie A 2026/2027 club definitions
SERIE_A_TEAMS_2026_2027 = {
    "ATA": "Atalanta",
    "BOL": "Bologna",
    "CAG": "Cagliari",
    "COM": "Como",
    "EMP": "Empoli",
    "FIO": "Fiorentina",
    "GEN": "Genoa",
    "INT": "Inter",
    "JUV": "Juventus",
    "LAZ": "Lazio",
    "LEC": "Lecce",
    "MIL": "Milan",
    "MON": "Monza",
    "NAP": "Napoli",
    "PAR": "Parma",
    "ROM": "Roma",
    "TOR": "Torino",
    "UDI": "Udinese",
    "VEN": "Venezia",
    "VER": "Verona",
}

CANONICAL_TEAM_NAMES = set(SERIE_A_TEAMS_2026_2027.values())
CANONICAL_TEAM_CODES = set(SERIE_A_TEAMS_2026_2027.keys())

PROMOTED_TEAMS = {"Como", "Parma", "Venezia"}
PROMOTED_CODES = {"COM", "PAR", "VEN"}

RELEGATED_TEAMS = {"Salernitana", "Sassuolo", "Frosinone"}
RELEGATED_CODES = {"SAL", "SAS", "FRO"}


def _resolve_file_path(*possible_names: str) -> Path:
    """Find the first existing file matching any of the possible names in data/."""
    for name in possible_names:
        p = DATA_DIR / name
        if p.is_file():
            return p
    # Default to the first name for error messages
    return DATA_DIR / possible_names[0]


class TestPipelineExecution(unittest.TestCase):
    """Verifies that the main manual update script executes with exit code 0."""

    def test_pipeline_execution_exit_code_zero(self):
        """Execute update_fanta_data.py and verify returncode == 0."""
        if not MAIN_SCRIPT.exists():
            self.skipTest(f"{MAIN_SCRIPT} not yet created by implementation worker.")

        result = subprocess.run(
            [sys.executable, str(MAIN_SCRIPT), "--all"],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"Pipeline failed with return code {result.returncode}.\nStderr: {result.stderr}\nStdout: {result.stdout}",
        )


class TestDataFileExistence(unittest.TestCase):
    """Verifies that all required JSON and CSV artifacts exist and are non-empty."""

    def test_all_expected_files_exist_and_non_empty(self):
        """Verify presence of players, lineups, calendar, teams, players_db, and sync_report."""
        expected_file_groups = [
            ("players.json",),
            ("players.csv",),
            ("probabili_formazioni.json", "lineups.json"),
            ("probabili_formazioni.csv", "lineups.csv"),
            ("calendario_serie_a.json", "calendar.json"),
            ("calendario_serie_a.csv", "calendar.csv"),
            ("teams.json",),
            ("teams.csv",),
            ("players_db.json",),
            ("sync_report.json",),
        ]

        missing_or_empty = []
        for group in expected_file_groups:
            resolved = _resolve_file_path(*group)
            if not resolved.exists():
                missing_or_empty.append(f"Missing: {' / '.join(group)}")
            elif resolved.stat().st_size == 0:
                missing_or_empty.append(f"Empty (0 bytes): {resolved.name}")

        self.assertEqual(
            len(missing_or_empty),
            0,
            f"Data file verification failed:\n" + "\n".join(missing_or_empty),
        )


class TestSerieATeamsIntegrity(unittest.TestCase):
    """Verifies strict adherence to Serie A 2026/2027 club composition."""

    def setUp(self):
        self.teams_json_path = _resolve_file_path("teams.json")
        self.teams_csv_path = _resolve_file_path("teams.csv")

    def test_teams_json_exact_20_clubs(self):
        """Verify teams.json contains exactly 20 clubs."""
        self.assertTrue(self.teams_json_path.exists(), f"{self.teams_json_path} missing")
        with open(self.teams_json_path, "r", encoding="utf-8") as f:
            teams = json.load(f)

        self.assertEqual(
            len(teams),
            20,
            f"Expected exactly 20 teams in {self.teams_json_path.name}, found {len(teams)}",
        )

        team_names = {t.get("name") for t in teams if isinstance(t, dict)}
        team_codes = {t.get("code") or t.get("id") for t in teams if isinstance(t, dict)}

        # Check all 20 canonical names are present
        missing_names = CANONICAL_TEAM_NAMES - team_names
        self.assertEqual(
            len(missing_names),
            0,
            f"Missing required Serie A 2026/27 teams in teams.json: {missing_names}",
        )

        # Check promoted teams present
        for promoted in PROMOTED_TEAMS:
            self.assertIn(
                promoted,
                team_names,
                f"Promoted club {promoted} must be present in Serie A 2026/27 teams.json",
            )

        # Check relegated teams strictly absent
        for relegated in RELEGATED_TEAMS:
            self.assertNotIn(
                relegated,
                team_names,
                f"Relegated club {relegated} must NOT be present in Serie A 2026/27 teams.json",
            )
        for code in RELEGATED_CODES:
            self.assertNotIn(
                code,
                team_codes,
                f"Relegated club code {code} must NOT be present in Serie A 2026/27 teams.json",
            )

    def test_teams_csv_exact_20_clubs(self):
        """Verify teams.csv contains exactly 20 rows matching the 20 clubs."""
        self.assertTrue(self.teams_csv_path.exists(), f"{self.teams_csv_path} missing")
        with open(self.teams_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(
            len(rows),
            20,
            f"Expected exactly 20 rows in {self.teams_csv_path.name}, found {len(rows)}",
        )

        csv_names = {r.get("name") for r in rows}
        csv_codes = {r.get("code") or r.get("id") for r in rows}

        self.assertEqual(
            CANONICAL_TEAM_NAMES,
            csv_names,
            f"teams.csv names do not match canonical 2026/27 clubs: {csv_names.symmetric_difference(CANONICAL_TEAM_NAMES)}",
        )
        self.assertTrue(
            PROMOTED_TEAMS.issubset(csv_names),
            f"Promoted clubs {PROMOTED_TEAMS} not found in teams.csv",
        )
        self.assertTrue(
            csv_names.isdisjoint(RELEGATED_TEAMS),
            f"Relegated clubs {RELEGATED_TEAMS.intersection(csv_names)} found in teams.csv",
        )


class TestPlayersDatasetIntegrity(unittest.TestCase):
    """Verifies player dataset count, role distributions, pricing, and schema."""

    def setUp(self):
        self.players_json_path = _resolve_file_path("players.json")
        self.players_csv_path = _resolve_file_path("players.csv")
        self.players_db_path = _resolve_file_path("players_db.json")

    def test_players_json_count_and_roles(self):
        """Verify >500 players, valid roles (P, D, C, A), and minimum role quotas."""
        self.assertTrue(self.players_json_path.exists(), "players.json missing")
        with open(self.players_json_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        self.assertGreaterEqual(
            len(players),
            500,
            f"Expected >= 500 players in players.json, found {len(players)}",
        )

        role_counts = {"P": 0, "D": 0, "C": 0, "A": 0}
        valid_roles = {"P", "D", "C", "A"}

        for p in players:
            nome = p.get("nome", "")
            squadra = p.get("squadra", "")
            ruolo = p.get("ruolo", "")

            # Role must be valid
            self.assertIn(
                ruolo,
                valid_roles,
                f"Player {nome} has invalid role '{ruolo}'. Expected one of {valid_roles}",
            )
            role_counts[ruolo] += 1

            # Squadra must be in 2026/27 clubs (not relegated)
            self.assertNotIn(
                squadra,
                RELEGATED_TEAMS,
                f"Player {nome} assigned to relegated club '{squadra}'",
            )

            # Pricing validation
            qa = p.get("qa") or p.get("quotazione_attuale") or p.get("quotazione") or 1
            fvm = p.get("fvm_1000") or p.get("fvm") or 1
            prezzo_target = p.get("prezzo_target") or 1

            self.assertGreaterEqual(
                int(qa), 1, f"Player {nome} has non-positive QA: {qa}"
            )
            self.assertGreaterEqual(
                int(fvm), 1, f"Player {nome} has non-positive FVM: {fvm}"
            )
            self.assertGreaterEqual(
                int(prezzo_target),
                1,
                f"Player {nome} has non-positive target price: {prezzo_target}",
            )

        # Verify role distribution minimums
        self.assertGreaterEqual(
            role_counts["P"], 50, f"Expected >= 50 Goalkeepers (P), found {role_counts['P']}"
        )
        self.assertGreaterEqual(
            role_counts["D"], 150, f"Expected >= 150 Defenders (D), found {role_counts['D']}"
        )
        self.assertGreaterEqual(
            role_counts["C"], 150, f"Expected >= 150 Midfielders (C), found {role_counts['C']}"
        )
        self.assertGreaterEqual(
            role_counts["A"], 100, f"Expected >= 100 Attackers (A), found {role_counts['A']}"
        )

    def test_players_db_compatibility_structure(self):
        """Verify players_db.json contains role keys P, D, C, A matching dashboard contract."""
        self.assertTrue(self.players_db_path.exists(), "players_db.json missing")
        with open(self.players_db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        self.assertIsInstance(db, dict, "players_db.json root must be a dict keyed by role")
        for role in ["P", "D", "C", "A"]:
            self.assertIn(role, db, f"Missing role key '{role}' in players_db.json")
            self.assertIsInstance(
                db[role], list, f"players_db['{role}'] must be a list of player dicts"
            )
            self.assertGreater(
                len(db[role]), 0, f"Role bucket '{role}' is unexpectedly empty"
            )

        total_db_players = sum(len(db[r]) for r in ["P", "D", "C", "A"])
        self.assertGreaterEqual(
            total_db_players,
            500,
            f"players_db.json total count {total_db_players} < 500",
        )


class TestLineupsDatasetIntegrity(unittest.TestCase):
    """Verifies probable lineups matchday fixtures, starting XI, and bench structure."""

    def setUp(self):
        self.lineups_json_path = _resolve_file_path(
            "probabili_formazioni.json", "lineups.json"
        )
        self.lineups_csv_path = _resolve_file_path(
            "probabili_formazioni.csv", "lineups.csv"
        )

    def test_lineups_10_matches_and_20_teams(self):
        """Verify lineups contain 10 matches covering all 20 Serie A clubs."""
        self.assertTrue(self.lineups_json_path.exists(), "Lineups JSON missing")
        with open(self.lineups_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = data.get("matches", []) if isinstance(data, dict) else data
        self.assertEqual(
            len(matches),
            10,
            f"Expected 10 matches in lineups JSON, found {len(matches)}",
        )

        participating_teams = set()

        for match in matches:
            home_team = match.get("home_team") or match.get("casa", {}).get("squadra")
            away_team = match.get("away_team") or match.get("trasferta", {}).get("squadra")

            self.assertIsNotNone(home_team, "Match missing home team")
            self.assertIsNotNone(away_team, "Match missing away team")
            self.assertNotEqual(home_team, away_team, "Home and away team cannot be identical")

            participating_teams.add(home_team)
            participating_teams.add(away_team)

            # Inspect home and away lineup structures
            for side in ["home_lineup", "away_lineup", "casa", "trasferta"]:
                if side in match:
                    lineup = match[side]
                    titolari = lineup.get("titolari", [])
                    self.assertEqual(
                        len(titolari),
                        11,
                        f"Team {lineup.get('squadra', side)} does not have exactly 11 starters (found {len(titolari)})",
                    )

                    # Verify at least 1 goalkeeper starter
                    gk_starters = [
                        p for p in titolari
                        if p.get("ruolo", "").upper() in ("P", "POR")
                    ]
                    self.assertEqual(
                        len(gk_starters),
                        1,
                        f"Team {lineup.get('squadra', side)} must have exactly 1 starting Goalkeeper, found {len(gk_starters)}",
                    )

                    # Verify bench is present
                    panchina = lineup.get("panchina", [])
                    self.assertIsInstance(
                        panchina, list, "Panchina must be a list of substitute players"
                    )

        self.assertEqual(
            len(participating_teams),
            20,
            f"Expected 20 unique teams across 10 matches, found {len(participating_teams)}: {participating_teams}",
        )


class TestCalendarDatasetIntegrity(unittest.TestCase):
    """Verifies season calendar 38 matchdays, 380 total fixtures, and schedule symmetry."""

    def setUp(self):
        self.calendar_json_path = _resolve_file_path(
            "calendario_serie_a.json", "calendar.json"
        )
        self.calendar_csv_path = _resolve_file_path(
            "calendario_serie_a.csv", "calendar.csv"
        )

    def test_calendar_38_giornate_and_380_matches(self):
        """Verify 38 giornate and exactly 380 total matches."""
        self.assertTrue(self.calendar_json_path.exists(), "Calendar JSON missing")
        with open(self.calendar_json_path, "r", encoding="utf-8") as f:
            calendar = json.load(f)

        self.assertEqual(
            len(calendar),
            380,
            f"Expected exactly 380 matches in calendar JSON, found {len(calendar)}",
        )

        matchdays = set()
        home_matches = {code: 0 for code in CANONICAL_TEAM_CODES}
        away_matches = {code: 0 for code in CANONICAL_TEAM_CODES}
        head_to_head_pairs = set()

        for m in calendar:
            giornata = m.get("matchday") or m.get("giornata")
            home = m.get("home_team_code") or m.get("squadra_casa")
            away = m.get("away_team_code") or m.get("squadra_trasferta")

            # Resolve team code if name was stored
            if home in CANONICAL_TEAM_NAMES:
                home = [k for k, v in SERIE_A_TEAMS_2026_2027.items() if v == home][0]
            if away in CANONICAL_TEAM_NAMES:
                away = [k for k, v in SERIE_A_TEAMS_2026_2027.items() if v == away][0]

            self.assertIn(
                home,
                CANONICAL_TEAM_CODES,
                f"Invalid or relegated home team in calendar: {home}",
            )
            self.assertIn(
                away,
                CANONICAL_TEAM_CODES,
                f"Invalid or relegated away team in calendar: {away}",
            )
            self.assertNotEqual(home, away, f"Match fixture has identical home and away team: {home}")

            matchdays.add(giornata)
            home_matches[home] = home_matches.get(home, 0) + 1
            away_matches[away] = away_matches.get(away, 0) + 1
            head_to_head_pairs.add((home, away))

        # Check all 38 matchdays exist
        self.assertEqual(
            len(matchdays),
            38,
            f"Expected 38 matchdays (giornate 1-38), found {len(matchdays)}",
        )

        # Check each team plays 19 home and 19 away matches
        for code in CANONICAL_TEAM_CODES:
            self.assertEqual(
                home_matches[code],
                19,
                f"Team {code} plays {home_matches[code]} home matches, expected 19",
            )
            self.assertEqual(
                away_matches[code],
                19,
                f"Team {code} plays {away_matches[code]} away matches, expected 19",
            )

        # Check all 380 ordered pairs (home, away) are unique
        self.assertEqual(
            len(head_to_head_pairs),
            380,
            f"Expected 380 unique (home, away) head-to-head pairings, found {len(head_to_head_pairs)}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
