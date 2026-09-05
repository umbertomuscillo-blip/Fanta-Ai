import unittest
import json
from pathlib import Path
from src.best_lineup import LineupOptimizer, calculate_goals, simulate_head_to_head
from src.injury_news_engine import InjuryNewsEngine

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

class TestSeasonFeatures(unittest.TestCase):
    def setUp(self):
        with open(WORKSPACE_ROOT / "data" / "official_league_synced.json") as f:
            self.league = json.load(f)["teams"]
        self.optimizer = LineupOptimizer()

    def test_official_bench_and_tribuna_constraints(self):
        belluaglioni = self.league["ibelluaglioni"]["players"]
        res = self.optimizer.optimize_lineup(belluaglioni, matchday=3, use_modifier=True)

        # Starters = 11
        self.assertEqual(len(res.starters), 11)
        # Bench = 11
        self.assertEqual(len(res.bench), 11)
        # Tribuna = 3 (since total roster is 25)
        self.assertEqual(len(res.tribuna), 3)

        # Role breakdown in bench: 2P, 3D, 3C, 3A
        role_counts = {"P": 0, "D": 0, "C": 0, "A": 0}
        for p in res.bench:
            role_counts[p.ruolo] += 1
        
        self.assertEqual(role_counts["P"], 2, "Bench must have exactly 2 goalkeepers")
        self.assertEqual(role_counts["D"], 3, "Bench must have exactly 3 defenders")
        self.assertEqual(role_counts["C"], 3, "Bench must have exactly 3 midfielders")
        self.assertEqual(role_counts["A"], 3, "Bench must have exactly 3 attackers")

    def test_modifier_brackets(self):
        # Test exact modifier values
        # <6 -> 0, 6.0-6.24 -> 1, 6.25-6.49 -> 2, 6.5-6.74 -> 3, 6.75-6.99 -> 4.5, >=7 -> 6
        mock_p = type("P", (), {"expected_mv": 6.0})()
        
        def make_defs(avg_target):
            # Target avg: (gk + d1 + d2 + d3) / 4 = avg_target
            # 6.0 + 3*d = 4*avg_target => d = (4*avg_target - 6)/3
            val = (4 * avg_target - 6.0) / 3.0
            return [type("D", (), {"expected_mv": val})() for _ in range(4)]

        b0, _ = self.optimizer.calculate_modifier_bonus(mock_p, make_defs(5.90))
        self.assertEqual(b0, 0.0)

        b1, _ = self.optimizer.calculate_modifier_bonus(mock_p, make_defs(6.10))
        self.assertEqual(b1, 1.0)

        b2, _ = self.optimizer.calculate_modifier_bonus(mock_p, make_defs(6.30))
        self.assertEqual(b2, 2.0)

        b3, _ = self.optimizer.calculate_modifier_bonus(mock_p, make_defs(6.60))
        self.assertEqual(b3, 3.0)

        b4_5, _ = self.optimizer.calculate_modifier_bonus(mock_p, make_defs(6.80))
        self.assertEqual(b4_5, 4.5)

        b6, _ = self.optimizer.calculate_modifier_bonus(mock_p, make_defs(7.10))
        self.assertEqual(b6, 6.0)

    def test_captain_selection(self):
        belluaglioni = self.league["ibelluaglioni"]["players"]
        res = self.optimizer.optimize_lineup(belluaglioni, matchday=3, use_modifier=True)
        self.assertIsNotNone(res.captain)
        self.assertIn(res.captain.nome, ["Malen", "Calhanoglu"])

    def test_calculate_goals(self):
        self.assertEqual(calculate_goals(65.5), 0)
        self.assertEqual(calculate_goals(66.0), 1)
        self.assertEqual(calculate_goals(71.9), 1)
        self.assertEqual(calculate_goals(72.0), 2)
        self.assertEqual(calculate_goals(77.9), 2)
        self.assertEqual(calculate_goals(78.0), 3)

    def test_simulate_head_to_head(self):
        micio = self.league["BAYERN MICIO"]["players"]
        belluaglioni = self.league["ibelluaglioni"]["players"]
        matchup = simulate_head_to_head(micio, belluaglioni, "BAYERN MICIO", "ibelluaglioni", matchday=3)

        self.assertIn("home", matchup)
        self.assertIn("away", matchup)
        self.assertEqual(matchup["result_string"], "0 - 2")
        self.assertGreater(matchup["away"]["score"], matchup["home"]["score"])

    def test_calendar_integrity(self):
        with open(WORKSPACE_ROOT / "data" / "fanta_calendario_ufficiale.json") as f:
            cal = json.load(f)
        self.assertEqual(len(cal), 36)
        for r_name, r_data in cal.items():
            self.assertEqual(len(r_data["matches"]), 5)

if __name__ == "__main__":
    unittest.main()
