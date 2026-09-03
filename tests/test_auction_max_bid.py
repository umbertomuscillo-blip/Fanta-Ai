#!/usr/bin/env python3
"""
Modular E2E Test Suite: tests/test_auction_max_bid.py
Fantacalcio 2026/2027 Advanced Suite - Auction Max Bid & Rival Tracker Engine

Mathematical verification of:
1. User Max Bid Formula: MaxBid = RemainingCredits - (RemainingSlots - 1)
2. Rival Maximum Spending Ceiling: RivalCeiling = RivalCredits - (RemainingRivalSlots - 1)
3. Winning Bid Threshold: TargetBid = TopRivalCeiling + 1 (capped by UserMaxBid)
4. Role Minimum Reserves (1 credit per empty slot across P, D, C, A)
5. Corner cases: Initial state (500 cr, 25 slots -> 476), final slot (1 slot -> full remaining budget),
   minimum budget (25 cr with 25 slots -> 1 cr max bid), exhausted budget.
6. Frontend JS formula equivalence in dashboard/index.html.
"""

import json
import re
import unittest
from pathlib import Path
from typing import Dict, List, Any, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_HTML = WORKSPACE_ROOT / "dashboard" / "index.html"


def calculate_max_bid(remaining_credits: int, remaining_slots: int) -> int:
    """
    Computes mathematical max bid for a fantasy manager.
    Every remaining empty slot requires at least 1 credit.
    """
    if remaining_slots <= 0:
        return 0
    if remaining_credits < remaining_slots:
        return 0
    return remaining_credits - (remaining_slots - 1)


def calculate_rival_ceiling(rival_credits: int, slots_bought: int, total_slots: int = 25) -> int:
    """
    Computes maximum credit a rival can bid on a single player.
    """
    rem_slots = total_slots - slots_bought
    if rem_slots <= 0:
        return 0
    if rival_credits < rem_slots:
        return 0
    return rival_credits - (rem_slots - 1)


def calculate_winning_bid_threshold(
    user_credits: int,
    user_slots_bought: int,
    rivals: List[Dict[str, int]],
    total_slots: int = 25
) -> Tuple[int, int, bool]:
    """
    Calculates:
    - user_max_bid
    - highest_rival_ceiling
    - can_win (bool)
    """
    user_rem_slots = total_slots - user_slots_bought
    user_max = calculate_max_bid(user_credits, user_rem_slots)

    highest_rival_max = 0
    for r in rivals:
        c = calculate_rival_ceiling(r["credits"], r.get("slots", 0), total_slots)
        if c > highest_rival_max:
            highest_rival_max = c

    can_win = user_max > highest_rival_max
    return user_max, highest_rival_max, can_win


def calculate_role_reserves(
    roster: Dict[str, List[Any]],
    limits: Dict[str, int] = None
) -> Dict[str, int]:
    """
    Computes minimum credits reserved for unfilled slots per role.
    Standard Fantacalcio roster: P=3, D=8, C=8, A=6 (Total=25).
    """
    if limits is None:
        limits = {"P": 3, "D": 8, "C": 8, "A": 6}

    reserves = {}
    for role, limit in limits.items():
        bought_count = len(roster.get(role, []))
        empty_count = max(0, limit - bought_count)
        reserves[role] = empty_count  # 1 credit minimum per empty slot

    reserves["TOTAL"] = sum(reserves[r] for r in limits)
    return reserves


class TestUserMaxBidCalculation(unittest.TestCase):
    """
    Mathematical tests for User Max Bid calculation.
    """

    def test_initial_auction_state_max_bid(self):
        """Initial state (500 credits, 25 empty slots): max bid must be exactly 476 credits."""
        max_bid = calculate_max_bid(remaining_credits=500, remaining_slots=25)
        # 500 - (25 - 1) = 500 - 24 = 476
        self.assertEqual(max_bid, 476)

    def test_single_slot_remaining_max_bid(self):
        """When 1 slot remains, manager can bid 100% of remaining credits."""
        max_bid = calculate_max_bid(remaining_credits=180, remaining_slots=1)
        # 180 - (1 - 1) = 180
        self.assertEqual(max_bid, 180)

    def test_intermediate_auction_scenarios(self):
        """Verify various intermediate credit and slot counts."""
        # Scenario A: 320 credits left, 15 slots remaining -> 320 - 14 = 306
        self.assertEqual(calculate_max_bid(320, 15), 306)

        # Scenario B: 85 credits left, 6 slots remaining -> 85 - 5 = 80
        self.assertEqual(calculate_max_bid(85, 6), 80)

        # Scenario C: 12 credits left, 4 slots remaining -> 12 - 3 = 9
        self.assertEqual(calculate_max_bid(12, 4), 9)

    def test_edge_case_minimum_credits_per_slot(self):
        """When remaining credits equals remaining slots, max bid is exactly 1."""
        self.assertEqual(calculate_max_bid(25, 25), 1)
        self.assertEqual(calculate_max_bid(10, 10), 1)
        self.assertEqual(calculate_max_bid(1, 1), 1)

    def test_edge_case_zero_slots_or_exhausted_credits(self):
        """When 0 slots left or credits < slots, max bid is 0."""
        self.assertEqual(calculate_max_bid(50, 0), 0)
        self.assertEqual(calculate_max_bid(5, 10), 0)
        self.assertEqual(calculate_max_bid(0, 5), 0)


class TestRivalCeilingAndWinningThreshold(unittest.TestCase):
    """
    Mathematical tests for rival ceiling tracker and winning bid calculations.
    """

    def setUp(self):
        # 9 League rivals in a 10-team league
        self.rivals = [
            {"name": "Rival 1 (Andrea)", "credits": 420, "slots": 4},
            {"name": "Rival 2 (Marco)", "credits": 310, "slots": 8},
            {"name": "Rival 3 (Luca)", "credits": 490, "slots": 1},
            {"name": "Rival 4 (Giovanni)", "credits": 250, "slots": 12},
            {"name": "Rival 5 (Matteo)", "credits": 180, "slots": 15},
            {"name": "Rival 6 (Simone)", "credits": 390, "slots": 6},
            {"name": "Rival 7 (Federico)", "credits": 440, "slots": 3},
            {"name": "Rival 8 (Lorenzo)", "credits": 110, "slots": 18},
            {"name": "Rival 9 (Davide)", "credits": 500, "slots": 0},
        ]

    def test_rival_spending_ceilings(self):
        """Verify spending ceilings for individual rivals."""
        # Rival 9: 500 credits, 0 slots -> 500 - 24 = 476
        self.assertEqual(calculate_rival_ceiling(500, 0), 476)

        # Rival 3: 490 credits, 1 slot bought (24 slots left) -> 490 - 23 = 467
        self.assertEqual(calculate_rival_ceiling(490, 1), 467)

        # Rival 8: 110 credits, 18 slots bought (7 slots left) -> 110 - 6 = 104
        self.assertEqual(calculate_rival_ceiling(110, 18), 104)

        # Rival with completed roster (25 slots): ceiling is 0
        self.assertEqual(calculate_rival_ceiling(50, 25), 0)

    def test_winning_bid_threshold_user_leading(self):
        """When user has higher ceiling than all rivals, user can guarantee victory."""
        user_credits = 490
        user_slots = 0  # User max bid = 490 - 24 = 466

        # Rival max is Rival 3: 490 credits, 1 slot -> ceiling = 467
        user_max, top_rival_max, can_win = calculate_winning_bid_threshold(user_credits, user_slots, self.rivals)
        self.assertEqual(user_max, 466)
        self.assertEqual(top_rival_max, 476)  # Rival 9 has 476
        self.assertFalse(can_win)

        # If user has 500 credits and 0 slots:
        user_max, top_rival_max, can_win = calculate_winning_bid_threshold(500, 0, [
            {"name": "Rival A", "credits": 450, "slots": 2}, # ceiling = 450 - 22 = 428
            {"name": "Rival B", "credits": 380, "slots": 5}, # ceiling = 380 - 19 = 361
        ])
        self.assertEqual(user_max, 476)
        self.assertEqual(top_rival_max, 428)
        self.assertTrue(can_win)
        winning_price = top_rival_max + 1
        self.assertEqual(winning_price, 429)
        self.assertLessEqual(winning_price, user_max)


class TestRoleReserves(unittest.TestCase):
    """
    Mathematical tests for role minimum reserves (1 cr per empty slot).
    """

    def test_role_reserves_unfilled_roster(self):
        """Empty roster requires 3 P + 8 D + 8 C + 6 A = 25 credits total reserve."""
        roster = {"P": [], "D": [], "C": [], "A": []}
        reserves = calculate_role_reserves(roster)

        self.assertEqual(reserves["P"], 3)
        self.assertEqual(reserves["D"], 8)
        self.assertEqual(reserves["C"], 8)
        self.assertEqual(reserves["A"], 6)
        self.assertEqual(reserves["TOTAL"], 25)

    def test_role_reserves_partially_filled_roster(self):
        """Partially filled roster reserves exactly 1 credit per empty slot."""
        roster = {
            "P": [{"name": "Svilar", "price": 40}, {"name": "Milinkovic-Savic", "price": 15}], # 1 left
            "D": [{"name": f"D_{i}", "price": 10} for i in range(5)], # 3 left
            "C": [{"name": f"C_{i}", "price": 15} for i in range(4)], # 4 left
            "A": [{"name": "Lautaro", "price": 180}], # 5 left
        }
        reserves = calculate_role_reserves(roster)

        self.assertEqual(reserves["P"], 1)
        self.assertEqual(reserves["D"], 3)
        self.assertEqual(reserves["C"], 4)
        self.assertEqual(reserves["A"], 5)
        self.assertEqual(reserves["TOTAL"], 13)


class TestDashboardFrontendEquivalence(unittest.TestCase):
    """
    Verifies that dashboard/index.html implements identical max bid logic.
    """

    def test_dashboard_html_contains_max_bid_formulas(self):
        """Verify dashboard/index.html source code contains max bid math."""
        self.assertTrue(DASHBOARD_HTML.is_file(), f"Missing {DASHBOARD_HTML}")
        with open(DASHBOARD_HTML, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Check for user max bid formula in JS
        self.assertIn("user-max-bid", html_content)
        self.assertIn("remainingCredits", html_content)
        self.assertIn("remainingSlots", html_content)

        # Match max bid ternary formula: remainingCredits - (remainingSlots - 1)
        pattern = r"remainingCredits\s*-\s*\(\s*remainingSlots\s*-\s*1\s*\)"
        self.assertIsNotNone(
            re.search(pattern, html_content),
            "dashboard/index.html must contain exact formula: remainingCredits - (remainingSlots - 1)"
        )

        # Check for rival max bid formula in JS: rivalMaxBid = remSlots > 0 ? (r.credits - (remSlots - 1)) : r.credits
        rival_pattern = r"r\.credits\s*-\s*\(\s*remSlots\s*-\s*1\s*\)"
        self.assertIsNotNone(
            re.search(rival_pattern, html_content),
            "dashboard/index.html must contain exact rival formula: r.credits - (remSlots - 1)"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
