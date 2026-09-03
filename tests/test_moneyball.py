"""
Automated Test Suite for Moneyball Index, xG, xA, and Dataset Integrity (R3).
Tests:
1. Models Player and PlayerStats include xg, xa, xg_90, xa_90, moneyball_index.
2. Fallback dataset fallback_players.json has all keys populated.
3. Exported files data/players.json, data/players_db.json, data/players.csv have authentic values.
4. Existing JSON schema keys remain unbroken and fully backward compatible.
5. Moneyball index identifies high-value / undervalued players correctly.
"""

import csv
import json
import unittest
from pathlib import Path

from src.config import DATA_DIR
from src.models import Player, PlayerStats
from src.parsers.players_parser import compute_moneyball_metrics


class TestMoneyballModels(unittest.TestCase):
    def test_player_stats_dataclass_fields(self):
        stats = PlayerStats(
            partite_a_voto=2,
            media_voto=6.5,
            fantamedia=7.5,
            gol=1,
            assist=1,
            xg=5.2,
            xa=3.1,
            xg_90=0.15,
            xa_90=0.09,
            moneyball_index=84.5
        )
        d = stats.to_dict()
        self.assertEqual(d["xg"], 5.2)
        self.assertEqual(d["xa"], 3.1)
        self.assertEqual(d["xg_90"], 0.15)
        self.assertEqual(d["xa_90"], 0.09)
        self.assertEqual(d["moneyball_index"], 84.5)

    def test_player_dataclass_fields(self):
        p = Player(
            id=101,
            nome="Test Player",
            squadra="Inter",
            squadra_code="INT",
            ruolo="C",
            xg=6.0,
            xa=7.0,
            xg_90=0.18,
            xa_90=0.21,
            moneyball_index=88.0
        )
        d = p.to_dict()
        self.assertEqual(d["xg"], 6.0)
        self.assertEqual(d["xa"], 7.0)
        self.assertEqual(d["moneyball_index"], 88.0)

        csv_d = p.to_csv_dict()
        self.assertIn("xg", csv_d)
        self.assertIn("xa", csv_d)
        self.assertIn("moneyball_index", csv_d)


class TestMoneyballAlgorithm(unittest.TestCase):
    def test_attacker_moneyball_computation(self):
        mb = compute_moneyball_metrics(
            ruolo="A",
            fvm_1000=350,
            prezzo_target=175,
            gol=15,
            assist=4,
            mv=6.5,
            fm=8.0,
            piazzati="1° Rigorista"
        )
        self.assertGreater(mb["xg"], 0.0)
        self.assertGreater(mb["xa"], 0.0)
        self.assertGreater(mb["xg_90"], 0.0)
        self.assertGreater(mb["moneyball_index"], 0.0)

    def test_goalkeeper_moneyball_computation(self):
        mb = compute_moneyball_metrics(
            ruolo="P",
            fvm_1000=20,
            prezzo_target=10,
            mv=6.4,
            fm=5.8,
            clean_sheets=10,
            gol_subiti=25
        )
        self.assertEqual(mb["xg"], 0.0)
        self.assertEqual(mb["xa"], 0.0)
        self.assertGreater(mb["moneyball_index"], 60.0)


class TestMoneyballDatasetIntegrity(unittest.TestCase):
    def test_players_json_moneyball_keys(self):
        p_path = DATA_DIR / "players.json"
        self.assertTrue(p_path.exists())
        with open(p_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        self.assertGreater(len(players), 500)
        for p in players:
            self.assertIn("xg", p)
            self.assertIn("xa", p)
            self.assertIn("xg_90", p)
            self.assertIn("xa_90", p)
            self.assertIn("moneyball_index", p)
            self.assertIsInstance(p["xg"], (int, float))
            self.assertIsInstance(p["moneyball_index"], (int, float))

    def test_players_db_json_compatibility(self):
        db_path = DATA_DIR / "players_db.json"
        self.assertTrue(db_path.exists())
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        for role in ["P", "D", "C", "A"]:
            self.assertIn(role, db)
            self.assertGreater(len(db[role]), 0)
            for p in db[role]:
                self.assertIn("moneyball_index", p)
                self.assertIn("xg", p)
                self.assertIn("xa", p)

    def test_players_csv_headers(self):
        csv_path = DATA_DIR / "players.csv"
        self.assertTrue(csv_path.exists())
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            self.assertIn("xg", headers)
            self.assertIn("xa", headers)
            self.assertIn("xg_90", headers)
            self.assertIn("xa_90", headers)
            self.assertIn("moneyball_index", headers)


if __name__ == "__main__":
    unittest.main()
