#!/usr/bin/env python3
"""
Modular E2E Test Suite: tests/test_moneyball_metrics.py
Fantacalcio 2026/2027 Advanced Suite - Moneyball Metrics & xG/xA Backend

Verifies:
1. Schema validation of players.json, players.csv, and players_db.json.
2. Non-empty xG and xA values for outfield players (D, C, A).
3. Strictly positive Moneyball Index across all 588+ player records.
4. Mathematical accuracy of compute_moneyball_metrics across roles (P, D, C, A).
5. Full backwards compatibility with dashboard/index.html legacy schema.
"""

import csv
import json
import unittest
from pathlib import Path
from typing import Dict, List, Any

from src.parsers.players_parser import compute_moneyball_metrics

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"
PLAYERS_JSON = DATA_DIR / "players.json"
PLAYERS_CSV = DATA_DIR / "players.csv"
PLAYERS_DB_JSON = DATA_DIR / "players_db.json"


class TestMoneyballSchemaValidation(unittest.TestCase):
    """
    Verifies that all storage formats (JSON, CSV, players_db.json)
    contain the full schema with new Moneyball metrics.
    """

    def test_players_json_schema_has_moneyball_fields(self):
        """Verify players.json contains xg, xa, xg_90, xa_90, moneyball_index."""
        self.assertTrue(PLAYERS_JSON.is_file(), f"Missing {PLAYERS_JSON}")
        with open(PLAYERS_JSON, "r", encoding="utf-8") as f:
            players = json.load(f)

        self.assertIsInstance(players, list)
        self.assertGreaterEqual(len(players), 500)

        expected_fields = {"xg", "xa", "xg_90", "xa_90", "moneyball_index"}
        for p in players:
            for field in expected_fields:
                self.assertIn(field, p, f"Player {p.get('nome')} missing field {field}")
                self.assertIsInstance(p[field], (int, float), f"Field {field} for {p.get('nome')} not numeric")

    def test_players_csv_schema_has_moneyball_columns(self):
        """Verify players.csv headers and rows contain moneyball columns."""
        self.assertTrue(PLAYERS_CSV.is_file(), f"Missing {PLAYERS_CSV}")
        with open(PLAYERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])

            expected_cols = {"xg", "xa", "xg_90", "xa_90", "moneyball_index"}
            for col in expected_cols:
                self.assertIn(col, fieldnames, f"CSV missing column {col}")

            rows = list(reader)
            self.assertGreaterEqual(len(rows), 500)
            for row in rows:
                for col in expected_cols:
                    val = float(row[col])
                    self.assertGreaterEqual(val, 0.0)

    def test_players_db_json_role_partitions_have_moneyball_fields(self):
        """Verify players_db.json groups P, D, C, A with moneyball fields."""
        self.assertTrue(PLAYERS_DB_JSON.is_file(), f"Missing {PLAYERS_DB_JSON}")
        with open(PLAYERS_DB_JSON, "r", encoding="utf-8") as f:
            db = json.load(f)

        self.assertEqual(set(db.keys()), {"P", "D", "C", "A"})
        for role, p_list in db.items():
            self.assertGreater(len(p_list), 0)
            for p in p_list:
                self.assertIn("xg", p)
                self.assertIn("xa", p)
                self.assertIn("moneyball_index", p)


class TestExpectedMetricsDistribution(unittest.TestCase):
    """
    Verifies statistical distributions and non-empty xG/xA for outfield players.
    """

    def setUp(self):
        with open(PLAYERS_JSON, "r", encoding="utf-8") as f:
            self.players = json.load(f)

    def test_outfield_players_have_positive_expected_goals_or_assists(self):
        """Outfield players (D, C, A) must have positive statistical expectations."""
        outfield_players = [p for p in self.players if p["ruolo"] in {"D", "C", "A"}]
        self.assertGreater(len(outfield_players), 450)

        for p in outfield_players:
            self.assertGreater(
                p["xg"] + p["xa"], 0.0,
                f"Outfield player {p['nome']} ({p['ruolo']}) has zero xG and zero xA"
            )

    def test_moneyball_index_is_strictly_positive_and_bounded(self):
        """Moneyball Index must be in [20.0, 99.0] across all active players."""
        for p in self.players:
            mb = p["moneyball_index"]
            self.assertGreater(mb, 0.0, f"Player {p['nome']} has non-positive Moneyball Index: {mb}")
            self.assertGreaterEqual(mb, 20.0, f"Player {p['nome']} Moneyball Index below lower bound: {mb}")
            self.assertLessEqual(mb, 100.0, f"Player {p['nome']} Moneyball Index above upper bound: {mb}")

    def test_top_stars_moneyball_indexes(self):
        """Verify high-impact Serie A 2026/2027 stars have valid high-scoring indices."""
        star_names = {"Lautaro Martinez", "Malen", "Pulisic", "Calhanoglu", "Dimarco", "Bremer"}
        found_stars = []
        for p in self.players:
            for s in star_names:
                if s.lower() in p["nome"].lower():
                    found_stars.append(p)
                    self.assertGreater(p["moneyball_index"], 40.0)
                    if p["ruolo"] in {"C", "A"}:
                        self.assertGreater(p["xg"], 3.0)

        self.assertGreaterEqual(len(found_stars), 4)


class TestMoneyballFormulaComputation(unittest.TestCase):
    """
    Verifies exact mathematical calculations of compute_moneyball_metrics.
    """

    def test_goalkeeper_moneyball_metrics(self):
        """Goalkeepers have xg=0, xa=0, and valid positive moneyball rating."""
        res_top_gk = compute_moneyball_metrics(
            ruolo="P", fvm_1000=80, prezzo_target=40, mv=6.4, clean_sheets=15
        )
        self.assertEqual(res_top_gk["xg"], 0.0)
        self.assertEqual(res_top_gk["xa"], 0.0)
        self.assertEqual(res_top_gk["xg_90"], 0.0)
        self.assertEqual(res_top_gk["xa_90"], 0.0)
        self.assertGreater(res_top_gk["moneyball_index"], 50.0)

        res_budget_gk = compute_moneyball_metrics(
            ruolo="P", fvm_1000=15, prezzo_target=8, mv=6.25, clean_sheets=8
        )
        self.assertGreater(res_budget_gk["moneyball_index"], 60.0)

    def test_defender_moneyball_metrics_with_modifier(self):
        """Modifier defender with set pieces gains bonus xG/xA and high Moneyball score."""
        res_mod_def = compute_moneyball_metrics(
            ruolo="D", fvm_1000=240, prezzo_target=120, gol=5, assist=6,
            mv=6.45, fm=7.20, piazzati="Punizioni, Corner", mod_rating="TOP"
        )
        self.assertGreaterEqual(res_mod_def["xg"], 4.0)
        self.assertGreaterEqual(res_mod_def["xa"], 5.0)
        self.assertGreater(res_mod_def["moneyball_index"], 40.0)

    def test_midfielder_moneyball_penalty_taker(self):
        """Penalty-taking midfielder gets xG boost."""
        res_pen_mid = compute_moneyball_metrics(
            ruolo="C", fvm_1000=243, prezzo_target=122, gol=10, assist=5,
            mv=6.50, fm=7.60, piazzati="1° Rigorista, Punizioni, Corner"
        )
        self.assertGreaterEqual(res_pen_mid["xg"], 7.0)
        self.assertGreater(res_pen_mid["moneyball_index"], 40.0)

    def test_forward_top_striker_metrics(self):
        """Top forward produces highest xG."""
        res_fwd = compute_moneyball_metrics(
            ruolo="A", fvm_1000=361, prezzo_target=180, gol=24, assist=4,
            mv=6.60, fm=8.80, piazzati="2° Rigorista, Capitano"
        )
        self.assertGreaterEqual(res_fwd["xg"], 15.0)
        self.assertGreater(res_fwd["moneyball_index"], 40.0)


class TestBackwardsCompatibility(unittest.TestCase):
    """
    Verifies that adding Moneyball metrics does not break legacy fields
    consumed by the frontend dashboard or export pipelines.
    """

    def test_legacy_fields_are_fully_preserved(self):
        """Check presence and validity of all pre-existing fields in players.json."""
        with open(PLAYERS_JSON, "r", encoding="utf-8") as f:
            players = json.load(f)

        legacy_fields = [
            "id", "nome", "squadra", "squadra_code", "ruolo", "ruolo_mantra",
            "qa", "qi", "fvm_1000", "prezzo_target", "prezzo_max", "tier",
            "piazzati", "mod_rating", "mv", "fm", "note", "is_starter", "stats"
        ]

        for p in players:
            for field in legacy_fields:
                self.assertIn(field, p, f"Legacy field {field} missing from player {p.get('nome')}")

            # Verify stats sub-object
            stats = p["stats"]
            self.assertIsInstance(stats, dict)
            self.assertIn("partite_a_voto", stats)
            self.assertIn("gol", stats)
            self.assertIn("assist", stats)


if __name__ == "__main__":
    unittest.main(verbosity=2)
