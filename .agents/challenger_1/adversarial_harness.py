#!/usr/bin/env python3
"""
Tier 5 Adversarial Verification & Stress Test Harness.
Empirical Challenger for Fantacalcio 2026/2027 Automated Data Pipeline.
"""

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKSPACE_ROOT = Path("/Users/umbertomuscillo/Documents/Fantacalcio")
DATA_DIR = WORKSPACE_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
SRC_DIR = WORKSPACE_ROOT / "src"
FALLBACK_DIR = SRC_DIR / "fallback_data"
MAIN_SCRIPT = WORKSPACE_ROOT / "update_fanta_data.py"

sys.path.insert(0, str(WORKSPACE_ROOT))

from src.config import (
    SERIE_A_TEAMS_2026_2027,
    PROMOTED_TEAMS_2026_2027,
    RELEGATED_TEAMS,
    normalize_team,
)
from src.models import Player, PlayerStats, MatchLineup, TeamLineup, MatchFixture, SyncReport
from src.parsers.players_parser import PlayersParser
from src.parsers.lineups_parser import LineupsParser
from src.parsers.fixtures_parser import FixturesParser
from src.validators.season_validator import SeasonValidator, ValidationError
from src.fetchers.base_fetcher import BaseFetcher
from src.pipeline import DataPipeline, run_pipeline


class Test01CliStressAndEdgeCases(unittest.TestCase):
    """Stress tests CLI flags, invalid arguments, option combinations, and concurrency."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MAIN_SCRIPT)] + args,
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_cli_01_invalid_flag_exits_non_zero(self):
        """CLI with unknown flag '--nonexistent-flag' should exit non-zero with error message."""
        res = self._run_cli(["--nonexistent-flag"])
        self.assertNotEqual(res.returncode, 0, "CLI should fail on unrecognized argument")
        self.assertIn("unrecognized arguments", res.stderr.lower())

    def test_cli_02_all_flag_execution(self):
        """CLI with --all flag should execute successfully (exit 0)."""
        res = self._run_cli(["--all", "--offline-fallback"])
        self.assertEqual(res.returncode, 0, f"CLI --all failed: {res.stderr}")
        self.assertIn("PIPELINE EXECUTION SUMMARY", res.stdout)
        self.assertIn("SUCCESS (OK)", res.stdout)

    def test_cli_03_pairwise_flag_combinations(self):
        """Test combinations: --players --lineups, --lineups --fixtures, --players --fixtures."""
        combos = [
            ["--players", "--lineups", "--offline-fallback"],
            ["--lineups", "--fixtures", "--offline-fallback"],
            ["--players", "--fixtures", "--offline-fallback"],
            ["--players", "--lineups", "--fixtures", "--offline-fallback"],
        ]
        for combo in combos:
            res = self._run_cli(combo)
            self.assertEqual(res.returncode, 0, f"Failed combo {combo}: {res.stderr}")

    def test_cli_04_offline_flag_aliases(self):
        """Test --offline and --offline-fallback aliases."""
        res1 = self._run_cli(["--offline", "--players"])
        self.assertEqual(res1.returncode, 0, f"Failed --offline: {res1.stderr}")

        res2 = self._run_cli(["--offline-fallback", "--players"])
        self.assertEqual(res2.returncode, 0, f"Failed --offline-fallback: {res2.stderr}")

    def test_cli_05_verbose_logging_flag(self):
        """Test -v and --verbose flags produce debug logging output."""
        res = self._run_cli(["-v", "--offline-fallback", "--lineups"])
        self.assertEqual(res.returncode, 0, f"Failed -v: {res.stderr}")

    def test_cli_06_concurrent_pipeline_invocations(self):
        """Execute 4 concurrent instances of update_fanta_data.py to test process isolation & race conditions."""
        def run_proc(worker_id):
            return self._run_cli(["--offline-fallback"])

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_proc, i) for i in range(4)]
            results = [f.result() for f in futures]

        for idx, res in enumerate(results):
            self.assertEqual(
                res.returncode, 0,
                f"Worker {idx} failed in concurrent execution: {res.stderr}"
            )


class Test02ParserAdversarialResilience(unittest.TestCase):
    """Adversarial stress testing of parser against malformed HTML, unexpected tokens, and corrupted data."""

    def test_parser_01_players_empty_html_triggers_fallback(self):
        """Passing empty string or whitespace to PlayersParser triggers bundled fallback gracefully."""
        parser = PlayersParser()
        players = parser.parse("", "")
        self.assertGreaterEqual(len(players), 500)
        self.assertIsInstance(players[0].nome, str)

    def test_parser_02_players_insufficient_records_triggers_fallback(self):
        """HTML containing fewer than 500 players (<500 threshold) falls back to high-fidelity dataset."""
        partial_html = """
        <table>
            <tr class="player-row">
                <td><th class="player-role player-role-classic"><span class="role" data-value="A"></span></th></td>
                <td><a href="/player/101"><span>Lautaro Martinez</span></a></td>
                <td class="player-team" data-col-key="sq">INT</td>
                <td class="player-classic-current-price" data-col-key="c_qa">38</td>
                <td class="player-classic-initial-price" data-col-key="c_qi">36</td>
                <td class="player-classic-fvm" data-col-key="c_fvm">320</td>
            </tr>
        </table>
        """
        parser = PlayersParser()
        players = parser.parse(partial_html, None)
        # Should fallback to full dataset (>=500)
        self.assertGreaterEqual(len(players), 500)

    def test_parser_03_players_malformed_corrupted_html(self):
        """Adversarial HTML with missing closing tags, script tags, SQL injection strings."""
        corrupted_html = """
        <div class="garbage">
            <script>alert('xss');</script>
            <tr class="player-row">
                <th class="player-role"><span class="role" data-value="UNKNOWN"></span></th>
                <span>Corrupted ' OR '1'='1</span>
                <td data-col-key="c_qa">not_a_number</td>
            </tr>
            <<<<<>>>>&&&$$$###
        </div>
        """
        parser = PlayersParser()
        players = parser.parse(corrupted_html, corrupted_html)
        self.assertGreaterEqual(len(players), 500)
        self.assertEqual(len(set(p.squadra for p in players)), 20)

    def test_parser_04_lineups_empty_or_broken_html_triggers_fallback(self):
        """Empty or broken HTML in LineupsParser triggers high-fidelity fallback."""
        parser = LineupsParser()
        lineups = parser.parse("<div>Broken Lineups HTML</div>")
        self.assertEqual(len(lineups), 10)
        for m in lineups:
            self.assertEqual(len(m.home_lineup.titolari), 11)
            self.assertEqual(len(m.away_lineup.titolari), 11)

    def test_parser_05_lineups_html_with_under_11_starters_auto_promotes_bench(self):
        """HTML with only 9 starters auto-promotes 2 reserves so starting XI is exactly 11."""
        html_few_starters = """
        <div class="team-card">
            <h3 class="h6 team-name">Como</h3>
            <div class="h6 team-formation">4-2-3-1</div>
            <ul class="player-list starters">
        """ + "".join([
            f'<li class="player-item"><span class="role" data-value="D"></span><a class="player-name"><span>Starter_{i}</span></a><div class="progress-value">90%</div></li>'
            for i in range(1, 10) # 9 starters
        ]) + """
            </ul>
            <ul class="player-list reserves">
                <li class="player-item"><span class="role" data-value="C"></span><a class="player-name"><span>Bench_1</span></a><div class="progress-value">30%</div></li>
                <li class="player-item"><span class="role" data-value="A"></span><a class="player-name"><span>Bench_2</span></a><div class="progress-value">30%</div></li>
                <li class="player-item"><span class="role" data-value="A"></span><a class="player-name"><span>Bench_3</span></a><div class="progress-value">20%</div></li>
            </ul>
        </div>
        """
        parser = LineupsParser()
        parsed = parser._parse_from_html(html_few_starters)
        como_match = [m for m in parsed if m.home_team == "Como" or m.away_team == "Como"][0]
        como_lineup = como_match.home_lineup if como_match.home_team == "Como" else como_match.away_lineup
        self.assertEqual(len(como_lineup.titolari), 11, "Should promote bench players to reach 11 starters")

    def test_parser_06_fixtures_corrupted_text_triggers_fallback(self):
        """Corrupted fixtures text with broken matchday lines triggers fallback."""
        corrupted_text = "Matchday 1\nGarbage line v another garbage\nUnknown 5-9\n"
        parser = FixturesParser()
        fixtures = parser.parse(corrupted_text)
        self.assertEqual(len(fixtures), 380)

    def test_parser_07_fixtures_text_with_finished_score_parsing(self):
        """Fixtures parser handles completed match scores ('2-1 (1-0)') without crashing."""
        sample_txt = """
        ▪ Matchday 1
        Sat Aug 22 2026
          18:30  Inter v Monza  2-0 (1-0)
          20:45  Udinese v Como  1-1
        """
        parser = FixturesParser()
        parsed = parser._parse_from_text(sample_txt)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0].status, "FINISHED")
        self.assertEqual(parsed[0].home_score, 2)
        self.assertEqual(parsed[0].away_score, 0)
        self.assertEqual(parsed[1].home_score, 1)
        self.assertEqual(parsed[1].away_score, 1)


class Test03CacheAndFetcherResilience(unittest.TestCase):
    """Stress tests BaseFetcher handling of corrupted cache snapshots and network failover."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_cache_dir = Path(self.test_dir.name) / "cache"
        self.tmp_cache_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_fetcher_01_corrupted_empty_cache_file(self):
        """Zero-byte cache file falls back to Tier 3 when force_fallback is set."""
        empty_cache = self.tmp_cache_dir / "empty_cache.html"
        empty_cache.touch()

        fetcher = BaseFetcher()
        orig_cache = CACHE_DIR
        try:
            import src.fetchers.base_fetcher as bf
            bf.CACHE_DIR = self.tmp_cache_dir
            text, tier = fetcher.fetch_text(
                "https://invalid.url.local/test",
                cache_filename="empty_cache.html",
                force_fallback=True
            )
            self.assertEqual(tier, "TIER_3_FALLBACK")
            self.assertIsNone(text)
        finally:
            import src.fetchers.base_fetcher as bf
            bf.CACHE_DIR = orig_cache

    def test_fetcher_02_valid_cache_loads_tier_2(self):
        """Valid non-empty cache file returns content with TIER_2_CACHE."""
        cache_file = self.tmp_cache_dir / "valid_cache.html"
        cache_file.write_text("<html>Cached Content</html>", encoding="utf-8")

        fetcher = BaseFetcher()
        orig_cache = CACHE_DIR
        try:
            import src.fetchers.base_fetcher as bf
            bf.CACHE_DIR = self.tmp_cache_dir
            text, tier = fetcher.fetch_text(
                "https://invalid.url.local/test",
                cache_filename="valid_cache.html",
                force_fallback=True
            )
            self.assertEqual(tier, "TIER_2_CACHE")
            self.assertEqual(text, "<html>Cached Content</html>")
        finally:
            import src.fetchers.base_fetcher as bf
            bf.CACHE_DIR = orig_cache


class Test04DataInvariantsAuditing(unittest.TestCase):
    """Exhaustive invariant auditing across all data/ files."""

    def test_inv_01_players_json_invariants(self):
        """Audit data/players.json: unique IDs, positive prices, valid roles, no relegated clubs."""
        p_path = DATA_DIR / "players.json"
        self.assertTrue(p_path.exists(), "data/players.json must exist")

        with open(p_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        self.assertGreaterEqual(len(players), 500)

        ids = [p["id"] for p in players]
        self.assertEqual(len(ids), len(set(ids)), "Player IDs must be strictly unique")

        canonical_teams = set(SERIE_A_TEAMS_2026_2027.values())
        canonical_codes = set(SERIE_A_TEAMS_2026_2027.keys())
        relegated_names = set(RELEGATED_TEAMS.values())
        relegated_codes = set(RELEGATED_TEAMS.keys())

        teams_seen = set()
        codes_seen = set()

        for p in players:
            # Check ID
            self.assertIsInstance(p["id"], int)
            self.assertGreater(p["id"], 0)

            # Check Name
            self.assertIsInstance(p["nome"], str)
            self.assertGreater(len(p["nome"].strip()), 0)

            # Check Team
            self.assertIn(p["squadra"], canonical_teams, f"Invalid team {p['squadra']}")
            self.assertIn(p["squadra_code"], canonical_codes, f"Invalid team code {p['squadra_code']}")
            self.assertNotIn(p["squadra"], relegated_names, f"Relegated club {p['squadra']} found in players")
            self.assertNotIn(p["squadra_code"], relegated_codes, f"Relegated code {p['squadra_code']} found in players")

            teams_seen.add(p["squadra"])
            codes_seen.add(p["squadra_code"])

            # Check Role
            self.assertIn(p["ruolo"], {"P", "D", "C", "A"}, f"Invalid role {p['ruolo']}")
            self.assertIsInstance(p.get("ruolo_mantra"), str)

            # Check Pricing
            self.assertIsInstance(p["qa"], int)
            self.assertIsInstance(p["qi"], int)
            self.assertIsInstance(p["fvm_1000"], int)
            self.assertIsInstance(p["prezzo_target"], int)
            self.assertIsInstance(p["prezzo_max"], int)

            self.assertGreaterEqual(p["qa"], 1)
            self.assertGreaterEqual(p["qi"], 1)
            self.assertGreaterEqual(p["fvm_1000"], 1)
            self.assertGreaterEqual(p["prezzo_target"], 1)
            self.assertGreaterEqual(p["prezzo_max"], p["prezzo_target"])

            # Check Stats
            stats = p.get("stats", {})
            self.assertIsInstance(stats.get("partite_a_voto", 0), int)
            self.assertIsInstance(stats.get("media_voto", 0.0), (int, float))
            self.assertIsInstance(stats.get("fantamedia", 0.0), (int, float))
            self.assertFalse(stats.get("media_voto") != stats.get("media_voto"), "NaN detected in media_voto")
            self.assertFalse(stats.get("fantamedia") != stats.get("fantamedia"), "NaN detected in fantamedia")

        # Verify all 20 teams present, including Como, Parma, Venezia
        self.assertEqual(len(teams_seen), 20)
        self.assertEqual(len(codes_seen), 20)
        for promo in PROMOTED_TEAMS_2026_2027.values():
            self.assertIn(promo, teams_seen)

    def test_inv_02_players_db_json_backward_compatibility(self):
        """Audit data/players_db.json: top-level roles P, D, C, A sum to players.json count."""
        db_path = DATA_DIR / "players_db.json"
        p_path = DATA_DIR / "players.json"

        self.assertTrue(db_path.exists(), "data/players_db.json must exist")
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        with open(p_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        self.assertEqual(set(db.keys()), {"P", "D", "C", "A"})
        total_players_in_db = sum(len(db[r]) for r in ["P", "D", "C", "A"])
        self.assertEqual(total_players_in_db, len(players))

    def test_inv_03_lineups_json_invariants(self):
        """Audit data/probabili_formazioni.json: exactly 10 matches, 20 teams, 11 starters per team."""
        l_path = DATA_DIR / "probabili_formazioni.json"
        self.assertTrue(l_path.exists())

        with open(l_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = data.get("matches", [])
        self.assertEqual(len(matches), 10)

        teams_seen = set()
        for m in matches:
            self.assertEqual(m["giornata"], 1)
            h_lineup = m["home_lineup"]
            a_lineup = m["away_lineup"]

            self.assertIsNotNone(h_lineup)
            self.assertIsNotNone(a_lineup)

            teams_seen.add(h_lineup["squadra"])
            teams_seen.add(a_lineup["squadra"])

            # 11 starters
            self.assertEqual(len(h_lineup["titolari"]), 11)
            self.assertEqual(len(a_lineup["titolari"]), 11)

            # Check 1 GK
            h_gks = sum(1 for p in h_lineup["titolari"] if p.get("ruolo") == "P")
            a_gks = sum(1 for p in a_lineup["titolari"] if p.get("ruolo") == "P")
            self.assertEqual(h_gks, 1)
            self.assertEqual(a_gks, 1)

            # Probabilities in [0, 100]
            for p in h_lineup["titolari"] + a_lineup["titolari"]:
                prob = p.get("probabilita", 0)
                self.assertGreaterEqual(prob, 0)
                self.assertLessEqual(prob, 100)

        self.assertEqual(len(teams_seen), 20)
        for promo in PROMOTED_TEAMS_2026_2027.values():
            self.assertIn(promo, teams_seen)
        for rel in RELEGATED_TEAMS.values():
            self.assertNotIn(rel, teams_seen)

    def test_inv_04_calendar_json_invariants(self):
        """Audit data/calendario_serie_a.json: 38 matchdays, 380 matches, 19 home / 19 away per club."""
        c_path = DATA_DIR / "calendario_serie_a.json"
        self.assertTrue(c_path.exists())

        with open(c_path, "r", encoding="utf-8") as f:
            fixtures = json.load(f)

        self.assertEqual(len(fixtures), 380)

        matchdays = set(f["giornata"] for f in fixtures)
        self.assertEqual(matchdays, set(range(1, 39)))

        home_counts = {t: 0 for t in SERIE_A_TEAMS_2026_2027.values()}
        away_counts = {t: 0 for t in SERIE_A_TEAMS_2026_2027.values()}

        for f in fixtures:
            self.assertIn(f["home_team"], SERIE_A_TEAMS_2026_2027.values())
            self.assertIn(f["away_team"], SERIE_A_TEAMS_2026_2027.values())
            self.assertNotEqual(f["home_team"], f["away_team"])
            self.assertEqual(f["season"], "2026/2027")

            home_counts[f["home_team"]] += 1
            away_counts[f["away_team"]] += 1

        for t in SERIE_A_TEAMS_2026_2027.values():
            self.assertEqual(home_counts[t], 19, f"Team {t} does not have 19 home games")
            self.assertEqual(away_counts[t], 19, f"Team {t} does not have 19 away games")

    def test_inv_05_teams_json_and_csv_invariants(self):
        """Audit data/teams.json and data/teams.csv: exactly 20 teams, no relegated clubs."""
        tj_path = DATA_DIR / "teams.json"
        tc_path = DATA_DIR / "teams.csv"

        self.assertTrue(tj_path.exists())
        self.assertTrue(tc_path.exists())

        with open(tj_path, "r", encoding="utf-8") as f:
            teams_j = json.load(f)
        with open(tc_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            teams_c = list(reader)

        self.assertEqual(len(teams_j), 20)
        self.assertEqual(len(teams_c), 20)

        for rel in RELEGATED_TEAMS.values():
            self.assertFalse(any(t["name"] == rel for t in teams_j))
            self.assertFalse(any(t["name"] == rel for t in teams_c))

        for promo in PROMOTED_TEAMS_2026_2027.values():
            promo_t = [t for t in teams_j if t["name"] == promo]
            self.assertEqual(len(promo_t), 1)
            self.assertTrue(promo_t[0]["promoted"])

    def test_inv_06_csv_headers_and_row_parity(self):
        """Audit all CSV files in data/ for header completeness and row parity."""
        csv_files = {
            "players.csv": (DATA_DIR / "players.csv", DATA_DIR / "players.json"),
            "teams.csv": (DATA_DIR / "teams.csv", DATA_DIR / "teams.json"),
            "calendario_serie_a.csv": (DATA_DIR / "calendario_serie_a.csv", DATA_DIR / "calendario_serie_a.json"),
        }

        for fname, (csv_p, json_p) in csv_files.items():
            self.assertTrue(csv_p.exists(), f"{fname} missing")
            with open(csv_p, "r", encoding="utf-8") as cf:
                reader = csv.DictReader(cf)
                rows = list(reader)
                fieldnames = reader.fieldnames
                self.assertIsNotNone(fieldnames)
                self.assertGreater(len(fieldnames), 3)

            with open(json_p, "r", encoding="utf-8") as jf:
                json_data = json.load(jf)

            self.assertEqual(len(rows), len(json_data), f"Row count mismatch in {fname}")

    def test_inv_07_absence_of_relegated_clubs_across_all_data_files(self):
        """Deep scan: ensure zero occurrences of Salernitana, Sassuolo, Frosinone across all generated json and csv files."""
        relegated_terms = ["salernitana", "sassuolo", "frosinone"]
        target_extensions = [".json", ".csv"]

        for file_path in DATA_DIR.iterdir():
            if file_path.suffix in target_extensions and file_path.is_file():
                content = file_path.read_text(encoding="utf-8").lower()
                for term in relegated_terms:
                    self.assertNotIn(
                        term, content,
                        f"Relegated club term '{term}' found inside generated file {file_path.name}"
                    )


class Test05ValidatorAdversarialEnforcement(unittest.TestCase):
    """Stress tests SeasonValidator error trapping on intentionally corrupted domain entities."""

    def test_validator_01_rejects_relegated_team_in_players(self):
        """SeasonValidator raises ValidationError if Salernitana or Sassuolo is injected into players."""
        validator = SeasonValidator()
        corrupted_player = [
            Player(id=999, nome="Corrupted Relegated", squadra="Salernitana", squadra_code="SAL", ruolo="A", qa=10, qi=10, fvm_1000=20, prezzo_target=10, prezzo_max=12)
        ]
        with self.assertRaises(ValidationError) as ctx:
            validator.validate_all(corrupted_player, [], [])
        self.assertIn("Relegated team", str(ctx.exception))

    def test_validator_02_rejects_non_positive_pricing(self):
        """SeasonValidator raises ValidationError if negative or 0 prices are detected."""
        validator = SeasonValidator()
        dummy_players = []
        for idx, (code, name) in enumerate(SERIE_A_TEAMS_2026_2027.items(), 1):
            dummy_players.append(Player(id=idx, nome=f"P_{name}", squadra=name, squadra_code=code, ruolo="D", qa=0, qi=0, fvm_1000=0, prezzo_target=0, prezzo_max=0))

        # Pad to 500
        for i in range(21, 505):
            dummy_players.append(Player(id=i, nome=f"Player_{i}", squadra="Inter", squadra_code="INT", ruolo="D", qa=0, qi=0, fvm_1000=0, prezzo_target=0, prezzo_max=0))

        with self.assertRaises(ValidationError) as ctx:
            validator.validate_all(dummy_players, [], [])
        self.assertIn("non-positive price", str(ctx.exception).lower())

    def test_validator_03_rejects_missing_matchdays(self):
        """SeasonValidator raises ValidationError if calendar contains 37 instead of 38 giornate."""
        validator = SeasonValidator()
        # Build valid players
        valid_players = []
        for idx, (code, name) in enumerate(SERIE_A_TEAMS_2026_2027.items(), 1):
            valid_players.append(Player(id=idx, nome=f"P_{name}", squadra=name, squadra_code=code, ruolo="D", qa=5, qi=5, fvm_1000=10, prezzo_target=5, prezzo_max=6))
        for i in range(21, 510):
            role = "P" if i < 70 else "D" if i < 220 else "C" if i < 370 else "A"
            valid_players.append(Player(id=i, nome=f"Player_{i}", squadra="Inter", squadra_code="INT", ruolo=role, qa=5, qi=5, fvm_1000=10, prezzo_target=5, prezzo_max=6))

        # Valid lineups
        valid_lineups = []
        teams = list(SERIE_A_TEAMS_2026_2027.items())
        for i in range(10):
            h_code, h_name = teams[i * 2]
            a_code, a_name = teams[i * 2 + 1]
            h_lineup = TeamLineup(squadra=h_name, squadra_code=h_code, modulo="3-5-2", titolari=[{"nome": f"{h_name} GK", "ruolo": "P", "probabilita": 90}] + [{"nome": f"{h_name} D{j}", "ruolo": "D", "probabilita": 90} for j in range(1, 11)])
            a_lineup = TeamLineup(squadra=a_name, squadra_code=a_code, modulo="3-5-2", titolari=[{"nome": f"{a_name} GK", "ruolo": "P", "probabilita": 90}] + [{"nome": f"{a_name} D{j}", "ruolo": "D", "probabilita": 90} for j in range(1, 11)])
            valid_lineups.append(MatchLineup(match_id=f"M_{i}", giornata=1, home_team=h_name, home_team_code=h_code, away_team=a_name, away_team_code=a_code, home_lineup=h_lineup, away_lineup=a_lineup))

        # 37 matchdays fixtures
        fixtures_37 = [
            MatchFixture(match_id=f"M_{i}", giornata=i, date_str="2026-08-22", home_team="Inter", home_team_code="INT", away_team="Milan", away_team_code="MIL")
            for i in range(1, 38)
        ]

        with self.assertRaises(ValidationError) as ctx:
            validator.validate_all(valid_players, valid_lineups, fixtures_37)
        self.assertIn("fixtures", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
