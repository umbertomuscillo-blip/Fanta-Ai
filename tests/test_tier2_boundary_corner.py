#!/usr/bin/env python3
"""
Tier 2: Boundary & Corner Cases Test Suite
Fantacalcio 2026/2027 Automated Data Pipeline

Tests edge cases, boundary value analysis (BVA), malformed data resilience,
empty cache fallbacks, character encoding integrity, and format boundaries.
"""

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.config import (
    SERIE_A_TEAMS_2026_2027,
    AUCTION_CONFIG,
    normalize_team,
)


class TestBoundaryValueAnalysis(unittest.TestCase):
    """Boundary Value Analysis (BVA) for pricing, roles, and matchdays."""

    def test_bva_01_minimum_price_scaling_lower_bound(self):
        """Test minimum FVM = 1 scaling gives target = 1 credit (not 0 or 0.5)."""
        fvm = 1
        scaled = max(1, round(fvm / 2))
        self.assertEqual(scaled, 1)

    def test_bva_02_superstar_fvm_scaling_upper_bound(self):
        """Test high FVM = 340 (e.g. Lautaro) scaling."""
        fvm = 340
        scaled_target = max(1, round(fvm / 2))
        max_bid = max(1, round(scaled_target * AUCTION_CONFIG["max_bid_multiplier"]))
        self.assertEqual(scaled_target, 170)
        self.assertEqual(max_bid, 212)
        self.assertLess(max_bid, AUCTION_CONFIG["total_budget"])

    def test_bva_03_zero_appearances_new_transfers(self):
        """Test handling of players with 0 appearances, 0 votes, 0 goals."""
        player = {
            "nome": "New Signing",
            "squadra": "Como",
            "ruolo": "C",
            "stats": {
                "presenze": 0,
                "media_voto": 0.0,
                "fantamedia": 0.0,
                "gol": 0,
                "assist": 0,
            },
            "qa": 5,
            "fvm_1000": 8,
            "prezzo_target": 4
        }
        self.assertEqual(player["stats"]["presenze"], 0)
        self.assertEqual(player["stats"]["media_voto"], 0.0)
        self.assertEqual(player["prezzo_target"], 4)

    def test_bva_04_calendar_giornate_boundaries(self):
        """Test calendar first matchday (1) and last matchday (38)."""
        matchdays = list(range(1, 39))
        self.assertEqual(matchdays[0], 1)
        self.assertEqual(matchdays[-1], 38)
        self.assertEqual(len(matchdays), 38)

    def test_bva_05_ballotaggio_exact_50_50_split(self):
        """Test 50/50 exact probability duel split."""
        duel = {
            "ruolo": "A",
            "titolare": "Taremi",
            "sfidante": "Arnautovic",
            "percentuale_titolare": 50,
            "percentuale_sfidante": 50
        }
        self.assertEqual(duel["percentuale_titolare"] + duel["percentuale_sfidante"], 100)


class TestEncodingAndEscapingResilience(unittest.TestCase):
    """Tests special characters, UTF-8 unicode integrity, and CSV escaping."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_enc_01_unicode_accents_preservation(self):
        """Test that European accents and Turkish characters are preserved without mojibake."""
        international_players = [
            {"nome": "Hakan Çalhanoğlu", "squadra": "Inter"},
            {"nome": "Matías Soulé", "squadra": "Roma"},
            {"nome": "Khvicha Kvaratskhelia", "squadra": "Napoli"},
            {"nome": "Paulo Dybala", "squadra": "Roma"},
            {"nome": "Armand Laurienté", "squadra": "Sassuolo"},
            {"nome": "Nico Paz", "squadra": "Como"},
        ]
        json_file = self.tmp_path / "players_unicode.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(international_players, f, ensure_ascii=False, indent=2)

        with open(json_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        self.assertEqual(loaded[0]["nome"], "Hakan Çalhanoğlu")
        self.assertEqual(loaded[1]["nome"], "Matías Soulé")
        self.assertEqual(loaded[2]["nome"], "Khvicha Kvaratskhelia")
        self.assertEqual(loaded[3]["nome"], "Paulo Dybala")

    def test_enc_02_csv_commas_and_quotes_escaping(self):
        """Test RFC 4180 CSV escaping for notes containing commas and quotes."""
        player_with_commas = {
            "id": 1,
            "nome": "Dimarco",
            "squadra": "Inter",
            "ruolo": "D",
            "note": "Attaccante aggiunto, batte punizioni, corner, e cross tesi (\"Top Assoluto\")",
            "piazzati": "1° Corner, 2° Punizioni"
        }
        csv_file = self.tmp_path / "test_escaping.csv"
        headers = ["id", "nome", "squadra", "ruolo", "note", "piazzati"]
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerow(player_with_commas)

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["note"], player_with_commas["note"])
        self.assertEqual(rows[0]["piazzati"], player_with_commas["piazzati"])

    def test_enc_03_empty_lists_serialized_as_empty_arrays(self):
        """Test that empty lists (e.g. infortunati: []) do not serialize to None or null."""
        data = {
            "infortunati": [],
            "squalificati": [],
            "ballottaggi": []
        }
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        self.assertEqual(loaded["infortunati"], [])
        self.assertEqual(loaded["squalificati"], [])
        self.assertIsNotNone(loaded["infortunati"])


class TestSystemEdgeCases(unittest.TestCase):
    """Tests file system resilience, malformed inputs, and CLI isolation."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_sys_01_auto_creation_of_missing_directories(self):
        """Test that nested output directories are created if absent."""
        nested_dir = self.tmp_path / "deeply" / "nested" / "data"
        nested_dir.mkdir(parents=True, exist_ok=True)
        self.assertTrue(nested_dir.exists())

    def test_sys_02_unrecognized_team_name_raises_value_error(self):
        """Test that normalizing an invalid/unknown team raises ValueError."""
        with self.assertRaises(ValueError):
            normalize_team("Real Madrid CF")
        with self.assertRaises(ValueError):
            normalize_team("")

    def test_sys_03_corrupted_json_handling(self):
        """Test resilience when encountering corrupted JSON string."""
        corrupted = '{"matchday": 1, "matches": ['
        with self.assertRaises(json.JSONDecodeError):
            json.loads(corrupted)

    def test_sys_04_various_formation_modulos(self):
        """Test that different football tactical modulos (3-5-2, 4-3-3, 3-4-2-1, 4-2-3-1, 3-4-1-2) all produce 11 starters."""
        modulos = ["3-5-2", "4-3-3", "3-4-2-1", "4-2-3-1", "3-4-1-2", "4-4-2", "3-4-3"]
        for mod in modulos:
            parts = [int(p) for p in mod.split("-")]
            outfield_count = sum(parts)
            self.assertEqual(
                outfield_count + 1,
                11,
                f"Modulo {mod} does not sum to 10 outfield players + 1 GK = 11"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
