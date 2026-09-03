"""
Adversarial Stress Test Suite for Auction Max Price Calculator & Moneyball Data Pipeline.
Executed by challenger_2 (Empirical Challenger).
"""

import csv
import itertools
import json
import math
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models import Player, PlayerStats, MatchLineup, MatchFixture, TeamLineup, Team, SyncReport
from src.parsers.players_parser import compute_moneyball_metrics, PlayersParser
from src.storage.json_exporter import JsonExporter
from src.storage.csv_exporter import CsvExporter
from src.config import SERIE_A_TEAMS_2026_2027, AUCTION_CONFIG


class TestAuctionMaxPriceFormulas(unittest.TestCase):
    """
    Mathematical stress tests for Auction Max Price calculations replicating JS logic in dashboard/index.html.
    """

    def calculate_max_bid(self, remaining_credits: int, remaining_slots: int) -> int:
        """Mirror JS: remainingSlots > 0 ? Math.max(1, (remainingCredits - (remainingSlots - 1))) : remainingCredits"""
        if remaining_slots > 0:
            return max(1, remaining_credits - (remaining_slots - 1))
        return remaining_credits

    def calculate_user_evaluator_max_bid(self, remaining_credits: int, remaining_slots: int) -> int:
        """Mirror evaluator userMaxBid JS: remainingSlots > 0 ? (remainingCredits - (remainingSlots - 1)) : remainingCredits"""
        if remaining_slots > 0:
            return remaining_credits - (remaining_slots - 1)
        return remaining_credits

    def calculate_rival_max_bid(self, credits: int, slots: int) -> int:
        """Mirror JS: const remSlots = 25 - r.slots; remSlots > 0 ? Math.max(1, (r.credits - (remSlots - 1))) : r.credits"""
        rem_slots = 25 - slots
        if rem_slots > 0:
            return max(1, credits - (rem_slots - 1))
        return credits

    def calculate_role_safety_reserve(self, user_roster: dict, target_role: str, remaining_credits: int) -> tuple[int, int]:
        """
        Mirror JS role reserve calculation in updateAuctionEvaluator:
        limits = { P: 3, D: 8, C: 8, A: 6 }
        """
        limits = {"P": 3, "D": 8, "C": 8, "A": 6}
        rem_p = max(0, limits["P"] - len(user_roster.get("P", [])))
        rem_d = max(0, limits["D"] - len(user_roster.get("D", [])))
        rem_c = max(0, limits["C"] - len(user_roster.get("C", [])))
        rem_a = max(0, limits["A"] - len(user_roster.get("A", [])))

        other_roles_reserve = 0
        if target_role == "P":
            other_roles_reserve = rem_d + rem_c + rem_a + max(0, rem_p - 1)
        elif target_role == "D":
            other_roles_reserve = rem_p + rem_c + rem_a + max(0, rem_d - 1)
        elif target_role == "C":
            other_roles_reserve = rem_p + rem_d + rem_a + max(0, rem_c - 1)
        elif target_role == "A":
            other_roles_reserve = rem_p + rem_d + rem_c + max(0, rem_a - 1)

        safe_max = max(1, remaining_credits - other_roles_reserve)
        return other_roles_reserve, safe_max

    def test_budget_edge_case_credits_equal_slots(self):
        """When remaining credits equals remaining slots (e.g. 24 credits, 24 slots), max bid must be exactly 1."""
        for slots in range(1, 26):
            credits = slots
            max_bid = self.calculate_max_bid(credits, slots)
            self.assertEqual(max_bid, 1, f"Failed for {credits} credits with {slots} slots")

    def test_budget_edge_case_single_slot_remaining(self):
        """When exactly 1 slot remains, user can spend all remaining credits (C - (1 - 1) = C)."""
        for credits in [1, 5, 50, 100, 350, 500]:
            max_bid = self.calculate_max_bid(credits, 1)
            self.assertEqual(max_bid, credits, f"Single slot max bid should equal {credits}, got {max_bid}")

    def test_budget_edge_case_bankruptcy_deficit(self):
        """When credits < slots (bankruptcy), evaluator flags negative/insufficient budget."""
        # e.g. 5 credits, 10 slots remaining -> userMaxBid = 5 - 9 = -4
        user_max_bid = self.calculate_user_evaluator_max_bid(5, 10)
        self.assertEqual(user_max_bid, -4)
        self.assertLess(user_max_bid, 1)
        
        # Any bid >= 1 should trigger budget warning: currentBid > userMaxBid
        current_bid = 1
        self.assertTrue(current_bid > user_max_bid)

    def test_budget_edge_case_all_slots_filled(self):
        """When 25/25 slots are filled (0 slots remaining), remaining slots is 0."""
        max_bid = self.calculate_max_bid(50, 0)
        self.assertEqual(max_bid, 50)

    def test_opponent_ceiling_zero_credits(self):
        """Opponent with 0 credits and remaining slots."""
        rival_max = self.calculate_rival_max_bid(0, 5)  # 20 slots remaining -> 0 - 19 = -19 -> max(1, -19) = 1
        self.assertEqual(rival_max, 1)

    def test_opponent_ceiling_massive_advantage(self):
        """Opponent has 500 cr (0 slots), user has 50 cr (20 slots)."""
        user_slots = 5
        user_rem_slots = 25 - user_slots  # 20
        user_credits = 50
        user_max = self.calculate_user_evaluator_max_bid(user_credits, user_rem_slots)  # 50 - 19 = 31

        rival_credits = 500
        rival_slots = 0
        rival_max = self.calculate_rival_max_bid(rival_credits, rival_slots)  # 500 - 24 = 476

        winning_threshold = rival_max + 1  # 477
        self.assertEqual(user_max, 31)
        self.assertEqual(rival_max, 476)
        self.assertEqual(winning_threshold, 477)
        self.assertLess(user_max, rival_max)
        self.assertLess(user_max, winning_threshold)

    def test_strategic_role_reserve_invariants(self):
        """Verify role safety reserves across different squad configurations."""
        # Configuration: empty roster (0/25)
        empty_roster = {"P": [], "D": [], "C": [], "A": []}
        for role, count in [("P", 3), ("D", 8), ("C", 8), ("A", 6)]:
            other_res, safe_max = self.calculate_role_safety_reserve(empty_roster, role, 500)
            # 25 total slots, so other roles + this role's other slots = 24 slots reserve
            self.assertEqual(other_res, 24)
            self.assertEqual(safe_max, 500 - 24)  # 476

        # Partially filled: 2 P, 7 D, 7 C, 5 A = 21 players bought, 4 slots left (1 per role)
        semi_roster = {
            "P": [{"name": f"P{i}", "price": 10} for i in range(2)],
            "D": [{"name": f"D{i}", "price": 10} for i in range(7)],
            "C": [{"name": f"C{i}", "price": 10} for i in range(7)],
            "A": [{"name": f"A{i}", "price": 10} for i in range(5)],
        }
        # Remaining slots: P:1, D:1, C:1, A:1 (total 4 remaining)
        # For any role evaluation: otherRolesReserve = 1 + 1 + 1 + 0 = 3 credits
        for role in ["P", "D", "C", "A"]:
            other_res, safe_max = self.calculate_role_safety_reserve(semi_roster, role, 100)
            self.assertEqual(other_res, 3)
            self.assertEqual(safe_max, 97)


class TestFullAuctionDraftSimulation(unittest.TestCase):
    """
    Simulates sequential 25-man auction drafts step-by-step.
    """

    def test_sequential_25_man_draft_invariants(self):
        """Simulate sequential purchase of 25 players under standard budget distribution."""
        limits = {"P": 3, "D": 8, "C": 8, "A": 6}
        roster = {"P": [], "D": [], "C": [] ,"A": []}
        total_budget = 500
        spent = 0

        # Purchase sequence with realistic price points (sum = 500)
        # P: 25, 1, 1 = 27
        # D: 15, 10, 5, 3, 1, 1, 1, 1 = 37
        # C: 35, 25, 15, 10, 5, 2, 1, 1 = 94
        # A: 200, 80, 40, 15, 5, 2 = 342
        # Total = 27 + 37 + 94 + 342 = 500
        purchases = [
            ("P", 25), ("P", 1), ("P", 1),
            ("D", 15), ("D", 10), ("D", 5), ("D", 3), ("D", 1), ("D", 1), ("D", 1), ("D", 1),
            ("C", 35), ("C", 25), ("C", 15), ("C", 10), ("C", 5), ("C", 2), ("C", 1), ("C", 1),
            ("A", 200), ("A", 80), ("A", 40), ("A", 15), ("A", 5), ("A", 2)
        ]
        self.assertEqual(sum(p[1] for p in purchases), 500)
        self.assertEqual(len(purchases), 25)

        for idx, (role, price) in enumerate(purchases):
            total_count = sum(len(roster[r]) for r in ["P", "D", "C", "A"])
            rem_slots = 25 - total_count
            rem_credits = total_budget - spent

            # Check invariant: remaining credits >= remaining slots before purchase
            self.assertGreaterEqual(rem_credits, rem_slots)

            # Check max bid
            max_bid = rem_credits - (rem_slots - 1) if rem_slots > 0 else rem_credits
            self.assertGreaterEqual(max_bid, price, f"Step {idx}: price {price} exceeds max_bid {max_bid}")

            # Execute purchase
            roster[role].append({"name": f"{role}_{len(roster[role])+1}", "price": price})
            spent += price

        # Post-draft assertions
        self.assertEqual(spent, 500)
        self.assertEqual(sum(len(roster[r]) for r in ["P", "D", "C", "A"]), 25)
        for r, lim in limits.items():
            self.assertEqual(len(roster[r]), lim)

    def test_superstar_first_pick_476_bid(self):
        """User bids maximum theoretical single bid of 476 cr on Lautaro, then fills 24 slots at 1 cr each."""
        roster = {"P": [], "D": [], "C": [] ,"A": []}
        total_budget = 500
        spent = 0

        # Step 1: Buy Lautaro at 476
        rem_slots = 25
        rem_credits = 500
        max_bid = rem_credits - (rem_slots - 1)  # 500 - 24 = 476
        self.assertEqual(max_bid, 476)

        roster["A"].append({"name": "Lautaro", "price": 476})
        spent += 476

        # Steps 2-25: 24 remaining slots, each must be bought at exactly 1 credit
        role_sequence = ["P"]*3 + ["D"]*8 + ["C"]*8 + ["A"]*5  # 24 slots
        for r in role_sequence:
            total_count = sum(len(roster[k]) for k in ["P", "D", "C", "A"])
            rem_slots = 25 - total_count
            rem_credits = total_budget - spent
            max_bid = rem_credits - (rem_slots - 1)
            self.assertEqual(max_bid, 1)  # Max bid is forced to 1

            roster[r].append({"name": f"{r}_slot", "price": 1})
            spent += 1

        self.assertEqual(spent, 500)
        self.assertEqual(sum(len(roster[k]) for k in ["P", "D", "C", "A"]), 25)


class TestDashboardModifierCalculation(unittest.TestCase):
    """
    Tests Modificatore Difesa algorithm in dashboard/index.html (avg of top 3 D + GK).
    """

    def calculate_modifier(self, p: float, d1: float, d2: float, d3: float, d4: float) -> tuple[float, int]:
        defs = sorted([d1, d2, d3, d4], reverse=True)
        top3_defs = defs[:3]
        avg = (p + top3_defs[0] + top3_defs[1] + top3_defs[2]) / 4.0

        if avg >= 7.00:
            bonus = 6
        elif avg >= 6.50:
            bonus = 3
        elif avg >= 6.00:
            bonus = 1
        else:
            bonus = 0

        return avg, bonus

    def test_mod_thresholds_exact(self):
        # 1. Under 6.00 -> 0 bonus
        avg, bonus = self.calculate_modifier(5.5, 6.0, 6.0, 6.0, 5.0)
        self.assertEqual(avg, 5.875)
        self.assertEqual(bonus, 0)

        # 2. Exactly 6.00 -> +1 bonus
        avg, bonus = self.calculate_modifier(6.0, 6.0, 6.0, 6.0, 5.0)
        self.assertEqual(avg, 6.000)
        self.assertEqual(bonus, 1)

        # 3. 6.499 -> +1 bonus
        avg, bonus = self.calculate_modifier(6.4, 6.5, 6.5, 6.5, 5.0)
        self.assertEqual(avg, 6.475)
        self.assertEqual(bonus, 1)

        # 4. Exactly 6.50 -> +3 bonus
        avg, bonus = self.calculate_modifier(6.5, 6.5, 6.5, 6.5, 5.0)
        self.assertEqual(avg, 6.500)
        self.assertEqual(bonus, 3)

        # 5. Exactly 7.00 -> +6 bonus
        avg, bonus = self.calculate_modifier(7.0, 7.0, 7.0, 7.0, 5.0)
        self.assertEqual(avg, 7.000)
        self.assertEqual(bonus, 6)

        # 6. Above 7.00 (e.g. 7.50) -> +6 bonus
        avg, bonus = self.calculate_modifier(7.5, 7.5, 7.5, 7.5, 5.0)
        self.assertEqual(avg, 7.500)
        self.assertEqual(bonus, 6)

    def test_mod_drops_worst_defender(self):
        # Defenders: 7.0, 6.5, 6.5, and a terrible 4.0
        # Worst defender (4.0) must be dropped, top 3 (7.0, 6.5, 6.5) kept
        avg, bonus = self.calculate_modifier(6.0, 7.0, 6.5, 6.5, 4.0)
        expected_avg = (6.0 + 7.0 + 6.5 + 6.5) / 4.0  # 26.0 / 4.0 = 6.5
        self.assertEqual(avg, expected_avg)
        self.assertEqual(bonus, 3)


class TestMoneyballDataPipeline(unittest.TestCase):
    """
    Stress tests for compute_moneyball_metrics and players data pipeline.
    """

    def test_zero_minutes_zero_stats_all_roles(self):
        """Players with 0 minutes, 0 goals, 0 assists, 0 FVM must not divide by zero and return valid 0-100 scores."""
        roles = ["P", "D", "C", "A"]
        for r in roles:
            metrics = compute_moneyball_metrics(
                ruolo=r,
                fvm_1000=0,
                prezzo_target=0,
                gol=0,
                assist=0,
                mv=0.0,
                fm=0.0,
                clean_sheets=0,
                gol_subiti=0
            )
            self.assertIn("xg", metrics)
            self.assertIn("xa", metrics)
            self.assertIn("xg_90", metrics)
            self.assertIn("xa_90", metrics)
            self.assertIn("moneyball_index", metrics)

            # Check finite and in range
            self.assertFalse(math.isnan(metrics["moneyball_index"]))
            self.assertFalse(math.isinf(metrics["moneyball_index"]))
            self.assertGreaterEqual(metrics["moneyball_index"], 0.0)
            self.assertLessEqual(metrics["moneyball_index"], 100.0)
            self.assertGreaterEqual(metrics["xg"], 0.0)
            self.assertGreaterEqual(metrics["xa"], 0.0)
            self.assertGreaterEqual(metrics["xg_90"], 0.0)
            self.assertGreaterEqual(metrics["xa_90"], 0.0)

    def test_goalkeeper_sub_30_fvm_edge_cases(self):
        """Test GK with fvm < 30 and varying target prices including 0, 1, 2, 5."""
        for cost in [0, 1, 2, 5, 20]:
            metrics = compute_moneyball_metrics(
                ruolo="P",
                fvm_1000=15,
                prezzo_target=cost,
                clean_sheets=3,
                mv=6.1
            )
            self.assertFalse(math.isnan(metrics["moneyball_index"]))
            self.assertGreaterEqual(metrics["moneyball_index"], 45.0)
            self.assertLessEqual(metrics["moneyball_index"], 98.0)

    def test_extreme_and_adversarial_inputs(self):
        """Test extreme high, negative, and unusual inputs."""
        extreme_cases = [
            {"ruolo": "A", "fvm_1000": 1000, "prezzo_target": 300, "gol": 40, "assist": 20, "mv": 8.5},
            {"ruolo": "D", "fvm_1000": 500, "prezzo_target": 150, "gol": 15, "assist": 10, "mv": 7.5, "mod_rating": "TOP_MOD"},
            {"ruolo": "C", "fvm_1000": 600, "prezzo_target": 200, "gol": 25, "assist": 18, "mv": 7.8, "piazzati": "1° Rigorista"},
            {"ruolo": "P", "fvm_1000": 85, "prezzo_target": 45, "clean_sheets": 20, "mv": 6.8},
            {"ruolo": "UNKNOWN", "fvm_1000": 10, "prezzo_target": 1, "gol": 0, "assist": 0, "mv": 0.0},
        ]
        for c in extreme_cases:
            res = compute_moneyball_metrics(**c)
            self.assertFalse(math.isnan(res["moneyball_index"]))
            self.assertFalse(math.isinf(res["moneyball_index"]))
            self.assertGreaterEqual(res["moneyball_index"], 0.0)
            self.assertLessEqual(res["moneyball_index"], 100.0)

    def test_exhaustive_moneyball_parameter_grid(self):
        """Run over 2000 combinations of roles, FVM, target prices, stats, and modifiers."""
        roles = ["P", "D", "C", "A", "UNKNOWN", ""]
        fvms = [0, 1, 10, 29, 30, 80, 200, 500]
        targets = [0, 1, 2, 5, 20, 50, 150]
        mvs = [0.0, 5.0, 5.8, 6.0, 6.5, 7.2]
        gols = [0, 1, 5, 15]

        count = 0
        for r, f, t, m, g in itertools.product(roles, fvms, targets, mvs, gols):
            res = compute_moneyball_metrics(
                ruolo=r,
                fvm_1000=f,
                prezzo_target=t,
                mv=m,
                gol=g,
                assist=max(0, g // 2),
                clean_sheets=g if r == "P" else 0
            )
            self.assertFalse(math.isnan(res["moneyball_index"]))
            self.assertFalse(math.isinf(res["moneyball_index"]))
            self.assertGreaterEqual(res["moneyball_index"], 0.0)
            self.assertLessEqual(res["moneyball_index"], 100.0)
            self.assertGreaterEqual(res["xg"], 0.0)
            self.assertGreaterEqual(res["xa"], 0.0)
            self.assertGreaterEqual(res["xg_90"], 0.0)
            self.assertGreaterEqual(res["xa_90"], 0.0)
            count += 1

        self.assertGreater(count, 2000)

    def test_existing_metrics_pass_through(self):
        """When existing xG/xA/moneyball are provided, they should be preserved correctly."""
        res = compute_moneyball_metrics(
            ruolo="A",
            fvm_1000=200,
            prezzo_target=50,
            existing_xg=14.5,
            existing_xa=6.2,
            existing_xg_90=0.45,
            existing_xa_90=0.19,
            existing_moneyball=88.5
        )
        self.assertEqual(res["xg"], 14.5)
        self.assertEqual(res["xa"], 6.2)
        self.assertEqual(res["xg_90"], 0.45)
        self.assertEqual(res["xa_90"], 0.19)
        self.assertEqual(res["moneyball_index"], 88.5)


class TestGeneratedDatasetsIntegrity(unittest.TestCase):
    """
    100% parseability, schema validation, and NaN/null checks on generated files.
    """

    def setUp(self):
        self.data_dir = PROJECT_ROOT / "data"

    def test_players_json_validity_and_no_nans(self):
        """Verify data/players.json is 100% valid JSON, has >500 items, and no nulls/NaNs."""
        path = self.data_dir / "players.json"
        self.assertTrue(path.exists(), f"{path} does not exist")

        with open(path, "r", encoding="utf-8") as f:
            players = json.load(f)

        self.assertIsInstance(players, list)
        self.assertGreaterEqual(len(players), 500)

        required_keys = [
            "id", "nome", "squadra", "squadra_code", "ruolo", "fvm_1000",
            "prezzo_target", "prezzo_max", "tier", "xg", "xa", "xg_90", "xa_90",
            "moneyball_index", "stats"
        ]

        valid_roles = {"P", "D", "C", "A"}
        valid_teams = set(SERIE_A_TEAMS_2026_2027.values())
        valid_codes = set(SERIE_A_TEAMS_2026_2027.keys())

        for idx, p in enumerate(players):
            for k in required_keys:
                self.assertIn(k, p, f"Player {idx} ({p.get('nome')}) missing key '{k}'")
                self.assertIsNotNone(p[k], f"Player {idx} key '{k}' is None")

            # Check types and ranges
            self.assertIn(p["ruolo"], valid_roles, f"Invalid role '{p['ruolo']}' for player {p['nome']}")
            self.assertIn(p["squadra"], valid_teams, f"Invalid team '{p['squadra']}' for player {p['nome']}")
            self.assertIn(p["squadra_code"], valid_codes, f"Invalid team code '{p['squadra_code']}' for player {p['nome']}")
            self.assertGreaterEqual(p["prezzo_target"], 1)
            self.assertGreaterEqual(p["prezzo_max"], p["prezzo_target"])
            self.assertFalse(math.isnan(p["moneyball_index"]))
            self.assertGreaterEqual(p["moneyball_index"], 0.0)
            self.assertLessEqual(p["moneyball_index"], 100.0)
            self.assertFalse(math.isnan(p["xg"]))
            self.assertFalse(math.isnan(p["xa"]))

    def test_players_db_json_validity_and_roles(self):
        """Verify data/players_db.json contains role-grouped arrays matching dashboard contract."""
        path = self.data_dir / "players_db.json"
        self.assertTrue(path.exists(), f"{path} does not exist")

        with open(path, "r", encoding="utf-8") as f:
            db = json.load(f)

        self.assertIsInstance(db, dict)
        for r in ["P", "D", "C", "A"]:
            self.assertIn(r, db, f"Role group {r} missing from players_db.json")
            self.assertIsInstance(db[r], list)
            self.assertGreater(len(db[r]), 0, f"Role group {r} is empty")

        total_in_db = sum(len(db[r]) for r in ["P", "D", "C", "A"])
        self.assertGreaterEqual(total_in_db, 500)

        # Check sample players
        for r in ["P", "D", "C", "A"]:
            for p in db[r]:
                self.assertEqual(p["ruolo"], r)
                self.assertIn("moneyball_index", p)
                self.assertIn("xg", p)
                self.assertIn("xa", p)
                self.assertFalse(math.isnan(p["moneyball_index"]))

    def test_players_csv_validity_and_columns(self):
        """Verify data/players.csv has correct columns, rows >= 500, and valid float values."""
        path = self.data_dir / "players.csv"
        self.assertTrue(path.exists(), f"{path} does not exist")

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertGreaterEqual(len(rows), 500)
        expected_cols = [
            "id", "nome", "squadra", "squadra_code", "ruolo", "prezzo_target",
            "prezzo_max", "fvm_1000", "xg", "xa", "xg_90", "xa_90", "moneyball_index"
        ]

        for col in expected_cols:
            self.assertIn(col, reader.fieldnames, f"CSV missing column '{col}'")

        for r in rows:
            self.assertTrue(r["nome"].strip(), "Empty player name found")
            self.assertIn(r["ruolo"], {"P", "D", "C", "A"})
            mb = float(r["moneyball_index"])
            xg = float(r["xg"])
            xa = float(r["xa"])
            self.assertFalse(math.isnan(mb))
            self.assertFalse(math.isnan(xg))
            self.assertFalse(math.isnan(xa))
            self.assertGreaterEqual(mb, 0.0)
            self.assertLessEqual(mb, 100.0)

    def test_cross_file_consistency(self):
        """Verify count and IDs match between players.json, players_db.json, and players.csv."""
        with open(self.data_dir / "players.json", "r", encoding="utf-8") as f:
            p_json = json.load(f)
        with open(self.data_dir / "players_db.json", "r", encoding="utf-8") as f:
            p_db = json.load(f)
        with open(self.data_dir / "players.csv", "r", encoding="utf-8") as f:
            p_csv = list(csv.DictReader(f))

        total_json = len(p_json)
        total_db = sum(len(p_db[r]) for r in ["P", "D", "C", "A"])
        total_csv = len(p_csv)

        self.assertEqual(total_json, total_db, "players.json and players_db.json count mismatch")
        self.assertEqual(total_json, total_csv, "players.json and players.csv count mismatch")


if __name__ == "__main__":
    unittest.main(verbosity=2)
