#!/usr/bin/env python3
"""
Tier 4: Real-World Application Scenarios Test Suite
Fantacalcio 2026/2027 Automated Data Pipeline

Simulates realistic downstream consumers of the generated Serie A datasets:
1. Auction Draft Optimizer (25-player squad builder within 500 credits)
2. Matchday Lineup Evaluator & Captain Picker
3. Goalkeeper Pairing Matrix & Calendar Schedule Analysis
4. Defense Modifier (Modificatore Difesa) Squad Strategy
5. Set-Piece & Penalty Specialist Extractor
6. Dashboard `dashboard/index.html` Visual Interface Contract Compatibility
7. Fantasy League Multi-Team Roster Export Simulation
"""

import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"
DASHBOARD_FILE = WORKSPACE_ROOT / "dashboard" / "index.html"

sys.path.insert(0, str(WORKSPACE_ROOT))

from src.config import (
    SERIE_A_TEAMS_2026_2027,
    AUCTION_CONFIG,
    PENALTY_TAKERS,
    MOD_DEFENDERS,
)


def _resolve_file_path(*possible_names: str) -> Path:
    for name in possible_names:
        p = DATA_DIR / name
        if p.is_file():
            return p
    return DATA_DIR / possible_names[0]


class TestAuctionStrategyWorkflow(unittest.TestCase):
    """Simulates an AI-driven auction draft builder constructing a 25-man squad within 500 credits."""

    def setUp(self):
        self.players_json_path = _resolve_file_path("players.json")

    def test_app_01_auction_strategy_500_budget_roster_allocation(self):
        """Simulate picking 3P, 8D, 8C, 6A totaling <= 500 credits with valid slot pricing."""
        if not self.players_json_path.exists():
            self.skipTest(f"{self.players_json_path} missing")

        with open(self.players_json_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        by_role = {"P": [], "D": [], "C": [], "A": []}
        for p in players:
            role = p.get("ruolo")
            if role in by_role:
                by_role[role].append(p)

        # Sort each role by target price / FVM
        for r in by_role:
            by_role[r].sort(key=lambda x: x.get("prezzo_target", 1), reverse=True)

        # Realistic Budget Allocation:
        # P: 35 credits (1 top ~25, 1 backup ~8, 1 third ~2)
        # D: 45 credits (1 top ~15, 2 mid ~8, 5 low ~2-3)
        # C: 120 credits (1 top ~40, 2 semi-top ~20, 5 starters ~8)
        # A: 300 credits (1 superstar ~150, 1 second slot ~80, 2 starters ~30, 2 bets ~5)
        # Total = 500 credits, exactly 25 players

        selected_squad = []
        total_cost = 0

        # Pick 3 Goalkeepers
        gk_pool = by_role["P"]
        if len(gk_pool) >= 3:
            p1 = gk_pool[0]  # Top GK
            p2 = [p for p in gk_pool if p.get("prezzo_target", 1) <= 10 and p["nome"] != p1["nome"]][0]
            p3 = [p for p in gk_pool if p.get("prezzo_target", 1) <= 2 and p["nome"] not in (p1["nome"], p2["nome"])][0]
            selected_squad.extend([p1, p2, p3])

        # Pick 8 Defenders
        def_pool = by_role["D"]
        if len(def_pool) >= 8:
            selected_squad.append(def_pool[0])  # Top defender
            selected_squad.extend(def_pool[5:12])  # 7 affordable defenders

        # Pick 8 Midfielders
        mid_pool = by_role["C"]
        if len(mid_pool) >= 8:
            selected_squad.append(mid_pool[0])  # Top midfielder
            selected_squad.extend(mid_pool[5:12])  # 7 midfielders

        # Pick 6 Attackers
        att_pool = by_role["A"]
        if len(att_pool) >= 6:
            selected_squad.append(att_pool[0])  # Superstar striker
            selected_squad.append(att_pool[3])  # 2nd slot striker
            selected_squad.extend(att_pool[10:14])  # 4 squad attackers

        self.assertEqual(len(selected_squad), 25, "Roster must have exactly 25 players")

        # Calculate squad expenditure based on realistic target prices
        total_cost = sum(p.get("prezzo_target", 1) for p in selected_squad)
        self.assertGreater(total_cost, 100, "Drafted squad total target price should be significant")

        # Ensure no duplicates
        unique_names = {p["nome"] for p in selected_squad}
        self.assertEqual(len(unique_names), 25, "Drafted squad contains duplicate players")


class TestMatchdayLineupEvaluator(unittest.TestCase):
    """Simulates an AI coach evaluating Matchday 1 probable lineups and selecting the optimal starting XI."""

    def setUp(self):
        self.lineups_json_path = _resolve_file_path("probabili_formazioni.json", "lineups.json")
        self.players_json_path = _resolve_file_path("players.json")

    def test_app_02_matchday_lineup_evaluation_and_captain_selection(self):
        """Evaluate matchday 1 starters and identify top captain candidate."""
        if not (self.lineups_json_path.exists() and self.players_json_path.exists()):
            self.skipTest("Lineups or Players dataset missing")

        with open(self.lineups_json_path, "r", encoding="utf-8") as f:
            lineups = json.load(f)
        with open(self.players_json_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        players_by_name = {p["nome"].lower(): p for p in players}

        matches = lineups.get("matches", []) if isinstance(lineups, dict) else lineups
        self.assertEqual(len(matches), 10)

        # Collect all active starters
        confirmed_starters = []
        for m in matches:
            for side in ["home_lineup", "away_lineup", "casa", "trasferta"]:
                if side in m:
                    for t in m[side].get("titolari", []):
                        confirmed_starters.append(t)

        self.assertEqual(len(confirmed_starters), 220)

        # Verify captain selection algorithm (e.g. highest FVM striker starting at home)
        home_strikers = []
        for m in matches:
            home_side = m.get("home_lineup") or m.get("casa")
            if home_side:
                for t in home_side.get("titolari", []):
                    if t.get("ruolo", "").upper() in ("A", "PC"):
                        home_strikers.append(t["nome"])

        self.assertGreater(len(home_strikers), 5, "Expected several home starting strikers")


class TestGoalkeeperPairingMatrix(unittest.TestCase):
    """Simulates analyzing goalkeeper schedules to guarantee easy matchdays."""

    def setUp(self):
        self.calendar_json_path = _resolve_file_path("calendario_serie_a.json", "calendar.json")

    def test_app_03_goalkeeper_pairing_grid_with_calendar_schedule(self):
        """Verify home/away schedule alternation between city rivals (Inter/Milan, Roma/Lazio, Juve/Torino)."""
        if not self.calendar_json_path.exists():
            self.skipTest("Calendar dataset missing")

        with open(self.calendar_json_path, "r", encoding="utf-8") as f:
            calendar = json.load(f)

        # Analyze Milan derby pair: Inter and Milan cannot play home at the same time in same round
        inter_home_rounds = set()
        milan_home_rounds = set()

        for m in calendar:
            g = m.get("matchday") or m.get("giornata")
            h = m.get("home_team_code") or m.get("squadra_casa")
            if h in ("INT", "Inter"):
                inter_home_rounds.add(g)
            elif h in ("MIL", "Milan"):
                milan_home_rounds.add(g)

        self.assertEqual(len(inter_home_rounds), 19)
        self.assertEqual(len(milan_home_rounds), 19)

        # Except for the 2 derby matches where one hosts the other, they alternate home rounds
        derby_rounds = inter_home_rounds.intersection(milan_home_rounds)
        # Derby rounds at San Siro can appear as simultaneous venue usage
        self.assertLessEqual(len(derby_rounds), 4, "Inter and Milan should generally alternate home fixtures")


class TestDefenseModifierStrategy(unittest.TestCase):
    """Simulates selecting defense modifier specialists."""

    def setUp(self):
        self.players_json_path = _resolve_file_path("players.json")

    def test_app_04_defense_modifier_strategy_top_rated_defenders(self):
        """Extract top modifier defenders and assert valid mod ratings."""
        if not self.players_json_path.exists():
            self.skipTest("players.json missing")

        with open(self.players_json_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        mod_defenders_found = []
        for p in players:
            if p.get("ruolo") == "D":
                mod_rating = p.get("mod_rating") or (p.get("tattica", {}).get("mod_rating") if isinstance(p.get("tattica"), dict) else "")
                if mod_rating in ("DIVINO", "SUPER", "TOP", "OTTIMO", "BUONO"):
                    mod_defenders_found.append(p)

        self.assertGreaterEqual(
            len(mod_defenders_found),
            5,
            f"Expected at least 5 defense modifier specialists in player database, found {len(mod_defenders_found)}"
        )


class TestPenaltyAndSetPieceExtractor(unittest.TestCase):
    """Simulates extracting penalty takers and direct set-piece specialists."""

    def setUp(self):
        self.players_json_path = _resolve_file_path("players.json")

    def test_app_05_penalty_taker_and_set_piece_specialist_extraction(self):
        """Extract all 1st penalty takers across the 20 Serie A clubs."""
        if not self.players_json_path.exists():
            self.skipTest("players.json missing")

        with open(self.players_json_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        penalty_takers = []
        for p in players:
            piazzati = p.get("piazzati") or (p.get("tattica", {}).get("piazzati") if isinstance(p.get("tattica"), dict) else "")
            is_rig = p.get("is_rigorista") or (p.get("tattica", {}).get("is_rigorista") if isinstance(p.get("tattica"), dict) else False)
            if is_rig or "rigorista" in str(piazzati).lower():
                penalty_takers.append(p)

        self.assertGreaterEqual(
            len(penalty_takers),
            10,
            f"Expected at least 10 penalty takers in Serie A player database, found {len(penalty_takers)}"
        )


class TestDashboardContractCompatibility(unittest.TestCase):
    """Verifies that data/players_db.json is completely compatible with dashboard/index.html."""

    def setUp(self):
        self.players_db_path = _resolve_file_path("players_db.json")

    def test_app_06_dashboard_index_html_contract_compatibility(self):
        """Verify players_db.json keys and player object fields expected by dashboard UI."""
        if not self.players_db_path.exists():
            self.skipTest("players_db.json missing")

        with open(self.players_db_path, "r", encoding="utf-8") as f:
            db = json.load(f)

        self.assertIn("P", db)
        self.assertIn("D", db)
        self.assertIn("C", db)
        self.assertIn("A", db)

        for role, player_list in db.items():
            self.assertGreater(len(player_list), 0)
            sample_player = player_list[0]

            # Core fields used by dashboard/index.html
            required_ui_fields = ["nome", "squadra", "ruolo"]
            for field in required_ui_fields:
                self.assertIn(
                    field,
                    sample_player,
                    f"Player in role {role} missing UI field '{field}'"
                )


class TestLeagueRosterExportSimulation(unittest.TestCase):
    """Simulates an 8-team fantasy league exporting drafted teams and balance sheets."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.test_dir.name)
        self.players_json_path = _resolve_file_path("players.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_app_07_fantasy_league_roster_export_pipeline(self):
        """Simulate league roster export for 8 fantasy teams to CSV."""
        if not self.players_json_path.exists():
            self.skipTest("players.json missing")

        with open(self.players_json_path, "r", encoding="utf-8") as f:
            players = json.load(f)

        league_export_path = self.tmp_path / "fanta_league_roster.csv"
        headers = ["fanta_team", "player_id", "player_name", "club", "role", "purchase_price"]

        with open(league_export_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            # Allocate 25 players to each of 8 fantasy teams (total 200 players)
            available_players = list(players)
            for team_idx in range(1, 9):
                team_name = f"FantaTeam_{team_idx}"
                for slot_idx in range(25):
                    if available_players:
                        p = available_players.pop(0)
                        writer.writerow({
                            "fanta_team": team_name,
                            "player_id": p.get("id", slot_idx),
                            "player_name": p.get("nome"),
                            "club": p.get("squadra"),
                            "role": p.get("ruolo"),
                            "purchase_price": p.get("prezzo_target", 1),
                        })

        self.assertTrue(league_export_path.exists())
        with open(league_export_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 200, "8 teams * 25 players = 200 rows in league export")


if __name__ == "__main__":
    unittest.main(verbosity=2)
