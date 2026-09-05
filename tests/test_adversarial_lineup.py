#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for Algoritmo 'Chi Schiero'
Fantacalcio 2026/2027 Lineup Optimizer (best_lineup.py & src/best_lineup.py)

Author: challenger_1 (Empirical Challenger)
Coverage:
1. Heavily depleted rosters & emergency formations (3-4-3, 5-4-1, 5-3-2, 3-5-2)
2. Exact floating-point boundaries for Modificatore Difesa (5.999, 6.000, 6.499, 6.500, 6.999, 7.000)
3. Defense modifier active vs inactive & 3/4/5 defenders invariant
4. 12-man bench ordering invariant (role order P->D->C->A + descending priority)
5. Corrupted, malformed, and adversarial input resilience
6. Strict zero-tolerance exclusion of injured and suspended players
7. Score monotonicity & tactical optimization veracity
8. CLI and JSON serialization stress testing
9. Empirical Bug Reproduction Harnesses (BUG-ADV-01, BUG-ADV-02, BUG-ADV-03, BUG-ADV-04)
"""

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.best_lineup import (
    LineupOptimizer,
    get_best_lineup,
    VALID_FORMATIONS,
    PlayerMatchContext,
    FormationResult,
    normalize_name
)


# ==============================================================================
# 1. HEAVILY DEPLETED ROSTERS & FORMATION CONSTRAINTS
# ==============================================================================
class TestDepletedRostersAndFormationInvariants(unittest.TestCase):
    """Stress tests on rosters with severe personnel constraints."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_exact_11_players_minimal_roster_343(self):
        """Minimal 11 players for 3-4-3: exactly 1 GK, 3 D, 4 C, 3 A."""
        roster = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.3},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.5},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.6},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.4},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.5},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.4},
            {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 6.5},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.5},
            {"nome": "Malen", "squadra": "Roma", "ruolo": "A", "mv": 6.5},
            {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 6.6},
        ]
        res = self.optimizer.optimize_lineup(roster, matchday=1, use_modifier=True)
        self.assertEqual(res.formation, "3-4-3")
        self.assertEqual(len(res.starters), 11)
        self.assertEqual(len(res.bench), 0)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "P"), 1)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "D"), 3)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "C"), 4)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "A"), 3)

    def test_exact_11_players_minimal_roster_541(self):
        """Minimal 11 players for 5-4-1: exactly 1 GK, 5 D, 4 C, 1 A."""
        roster = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.3},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.5},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.6},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.4},
            {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.4},
            {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "mv": 6.4},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.5},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.4},
            {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 6.5},
            {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 6.6},
        ]
        res = self.optimizer.optimize_lineup(roster, matchday=1, use_modifier=True)
        self.assertEqual(res.formation, "5-4-1")
        self.assertEqual(len(res.starters), 11)
        self.assertEqual(len(res.bench), 0)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "D"), 5)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "C"), 4)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "A"), 1)

    def test_exact_11_players_minimal_roster_532(self):
        """Minimal 11 players for 5-3-2: exactly 1 GK, 5 D, 3 C, 2 A."""
        roster = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.3},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.5},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.6},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.4},
            {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.4},
            {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "mv": 6.4},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.5},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.4},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.5},
            {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 6.6},
        ]
        res = self.optimizer.optimize_lineup(roster, matchday=1, use_modifier=True)
        self.assertEqual(res.formation, "5-3-2")
        self.assertEqual(len(res.starters), 11)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "D"), 5)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "C"), 3)
        self.assertEqual(sum(1 for s in res.starters if s.ruolo == "A"), 2)

    def test_insufficient_total_players_graceful_fallback(self):
        """When fewer than 11 fit players exist in roster, graceful fallback without unhandled exception."""
        roster = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.3},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.5},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.6},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5},
            {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 6.6},
        ]
        res = self.optimizer.optimize_lineup(roster, matchday=1, use_modifier=True)
        self.assertIsNotNone(res)
        self.assertEqual(len(res.starters), 5)
        self.assertEqual(len(res.bench), 0)


# ==============================================================================
# 2. EXACT FLOATING-POINT BOUNDARIES FOR MODIFICATORE DIFESA
# ==============================================================================
class TestModificatoreDifesaExactBoundaries(unittest.TestCase):
    """Stress tests on exact boundary floating point values for Modificatore Difesa."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def _create_def_unit(self, gk_mv: float, d1_mv: float, d2_mv: float, d3_mv: float, d4_mv: float = 5.0):
        gk = PlayerMatchContext(id=1, nome="GK", ruolo="P", squadra="Inter", squadra_code="INT", expected_mv=gk_mv)
        defs = [
            PlayerMatchContext(id=2, nome="D1", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=d1_mv),
            PlayerMatchContext(id=3, nome="D2", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=d2_mv),
            PlayerMatchContext(id=4, nome="D3", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=d3_mv),
            PlayerMatchContext(id=5, nome="D4", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=d4_mv),
        ]
        return gk, defs

    def test_boundary_5_999_vs_6_000(self):
        """Average 5.999 gives 0 bonus; Average 6.000 gives +1.0 bonus."""
        gk, defs_5999 = self._create_def_unit(6.0, 6.0, 6.0, 5.996)
        bonus_5999, avg_5999 = self.optimizer.calculate_modifier_bonus(gk, defs_5999)
        self.assertAlmostEqual(avg_5999, 5.999, places=3)
        self.assertEqual(bonus_5999, 0.0)

        gk, defs_6000 = self._create_def_unit(6.0, 6.0, 6.0, 6.0)
        bonus_6000, avg_6000 = self.optimizer.calculate_modifier_bonus(gk, defs_6000)
        self.assertAlmostEqual(avg_6000, 6.000, places=3)
        self.assertEqual(bonus_6000, 1.0)

    def test_boundary_6_499_vs_6_500(self):
        """Average 6.499 gives +2.0 bonus (official 5-tier); Average 6.500 gives +3.0 bonus."""
        gk, defs_6499 = self._create_def_unit(6.5, 6.5, 6.5, 6.496)
        bonus_6499, avg_6499 = self.optimizer.calculate_modifier_bonus(gk, defs_6499)
        self.assertAlmostEqual(avg_6499, 6.499, places=3)
        self.assertEqual(bonus_6499, 2.0)

        gk, defs_6500 = self._create_def_unit(6.5, 6.5, 6.5, 6.5)
        bonus_6500, avg_6500 = self.optimizer.calculate_modifier_bonus(gk, defs_6500)
        self.assertAlmostEqual(avg_6500, 6.500, places=3)
        self.assertEqual(bonus_6500, 3.0)

    def test_boundary_6_999_vs_7_000(self):
        """Average 6.999 gives +4.5 bonus (official 5-tier); Average 7.000 gives +6.0 bonus."""
        gk, defs_6999 = self._create_def_unit(7.0, 7.0, 7.0, 6.996)
        bonus_6999, avg_6999 = self.optimizer.calculate_modifier_bonus(gk, defs_6999)
        self.assertAlmostEqual(avg_6999, 6.999, places=3)
        self.assertEqual(bonus_6999, 4.5)

        gk, defs_7000 = self._create_def_unit(7.0, 7.0, 7.0, 7.0)
        bonus_7000, avg_7000 = self.optimizer.calculate_modifier_bonus(gk, defs_7000)
        self.assertAlmostEqual(avg_7000, 7.000, places=3)
        self.assertEqual(bonus_7000, 6.0)

    def test_modifier_only_uses_top_three_defenders_when_five_defenders_fielded(self):
        """When 5 defenders are fielded, 4th and 5th lowest defender votes must not drag down average."""
        gk = PlayerMatchContext(id=1, nome="GK", ruolo="P", squadra="Inter", squadra_code="INT", expected_mv=7.0)
        defs = [
            PlayerMatchContext(id=2, nome="TopD1", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=7.0),
            PlayerMatchContext(id=3, nome="TopD2", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=7.0),
            PlayerMatchContext(id=4, nome="TopD3", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=7.0),
            PlayerMatchContext(id=5, nome="FlopD4", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=4.0),
            PlayerMatchContext(id=6, nome="FlopD5", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=3.0),
        ]
        bonus, avg = self.optimizer.calculate_modifier_bonus(gk, defs)
        self.assertEqual(avg, 7.0)
        self.assertEqual(bonus, 6.0)


# ==============================================================================
# 3. DEFENSE MODIFIER ACTIVE VS INACTIVE & 3/4/5 DEFENDER INVARIANTS
# ==============================================================================
class TestDefenseModifierToggleAndTacticalImpact(unittest.TestCase):
    """Stress tests on optimizer behavior when modifier is active vs disabled."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_use_modifier_false_completely_disables_modifier_bonus(self):
        """When use_modifier=False, bonus is strictly 0.0 even with God-tier defenders."""
        roster = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 7.5},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 7.5},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 7.5},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 7.5},
            {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 7.5},
            {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "mv": 7.5},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.5},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.4},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.5},
            {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 6.6},
        ]
        res_no_mod = self.optimizer.optimize_lineup(roster, matchday=1, use_modifier=False)
        self.assertEqual(res_no_mod.modificatore_bonus, 0.0)

        res_with_mod = self.optimizer.optimize_lineup(roster, matchday=1, use_modifier=True)
        self.assertEqual(res_with_mod.modificatore_bonus, 6.0)

    def test_three_defender_formation_never_yields_modifier_bonus(self):
        """In 3-4-3 or 3-5-2, modifier bonus must strictly be 0.0."""
        roster = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 7.5},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 7.5},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 7.5},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 7.5},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 7.5, "xg": 10.0},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 7.5, "xg": 10.0},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 7.5, "xg": 10.0},
            {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 7.5, "xg": 10.0},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 7.5, "xg": 20.0},
            {"nome": "Malen", "squadra": "Roma", "ruolo": "A", "mv": 7.5, "xg": 20.0},
            {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 7.5, "xg": 20.0},
        ]
        res = self.optimizer.optimize_lineup(roster, matchday=1, use_modifier=True)
        if res.formation in ["3-4-3", "3-5-2"]:
            self.assertEqual(res.modificatore_bonus, 0.0)


# ==============================================================================
# 4. BENCH ORDERING INVARIANT (12 BENCH SLOTS, ROLE ORDER P->D->C->A, PRIORITY)
# ==============================================================================
class TestBenchOrderingInvariants(unittest.TestCase):
    """Stress tests on bench composition, role partition ordering, and priority."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_bench_role_partition_and_priority_invariants(self):
        """
        Verify that:
        1. Bench length <= 12.
        2. Bench roles strictly follow the sequence [P, ..., D, ..., C, ..., A].
        3. Within each role, players are sorted descending by expected_score.
        4. No starters are on the bench.
        5. No injured players are on the bench.
        """
        squad = [{"id": 100 + i, "nome": f"GK_{i}", "squadra": "Roma", "ruolo": "P", "mv": 5.5 + (i * 0.3)} for i in range(4)]
        squad += [{"id": 200 + i, "nome": f"DEF_{i}", "squadra": "Inter", "ruolo": "D", "mv": 5.5 + (i * 0.15), "xg": i * 0.5} for i in range(10)]
        squad += [{"id": 300 + i, "nome": f"MID_{i}", "squadra": "Milan", "ruolo": "C", "mv": 5.5 + (i * 0.15), "xg": i * 0.8} for i in range(10)]
        squad += [{"id": 400 + i, "nome": f"ATT_{i}", "squadra": "Juventus", "ruolo": "A", "mv": 5.5 + (i * 0.15), "xg": i * 1.5} for i in range(6)]

        res = self.optimizer.optimize_lineup(squad, matchday=1, use_modifier=True)
        self.assertEqual(len(res.starters), 11)
        self.assertLessEqual(len(res.bench), 12)

        starter_names = {s.nome for s in res.starters}
        bench_names = [b.nome for b in res.bench]
        self.assertEqual(len(starter_names.intersection(set(bench_names))), 0)

        role_order_map = {"P": 0, "D": 1, "C": 2, "A": 3}
        bench_role_indices = [role_order_map[b.ruolo] for b in res.bench]
        for i in range(len(bench_role_indices) - 1):
            self.assertLessEqual(
                bench_role_indices[i],
                bench_role_indices[i + 1],
                f"Bench role order violation at index {i}: {res.bench[i].ruolo} before {res.bench[i+1].ruolo}"
            )

        by_role = {"P": [], "D": [], "C": [], "A": []}
        for b in res.bench:
            by_role[b.ruolo].append(b.expected_score)

        for role, scores in by_role.items():
            for i in range(len(scores) - 1):
                self.assertGreaterEqual(
                    scores[i],
                    scores[i + 1],
                    f"Bench priority violation in role {role}: score {scores[i]} should be >= {scores[i+1]}"
                )


# ==============================================================================
# 5. CORRUPTED, MALFORMED, AND ADVERSARIAL INPUT RESILIENCE
# ==============================================================================
class TestMalformedInputResilience(unittest.TestCase):
    """Stress tests on corrupted, empty, or malicious roster inputs."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_unknown_player_names_fallback_gracefully(self):
        """Unknown or synthetic player names are parsed with sensible defaults without crash."""
        synthetic_squad = [
            {"nome": "Alien Goalkeeper", "ruolo": "P"},
            {"nome": "Alien Defender 1", "ruolo": "D"},
            {"nome": "Alien Defender 2", "ruolo": "D"},
            {"nome": "Alien Defender 3", "ruolo": "D"},
            {"nome": "Alien Defender 4", "ruolo": "D"},
            {"nome": "Alien Midfielder 1", "ruolo": "C"},
            {"nome": "Alien Midfielder 2", "ruolo": "C"},
            {"nome": "Alien Midfielder 3", "ruolo": "C"},
            {"nome": "Alien Midfielder 4", "ruolo": "C"},
            {"nome": "Alien Striker 1", "ruolo": "A"},
            {"nome": "Alien Striker 2", "ruolo": "A"},
        ]
        res = self.optimizer.optimize_lineup(synthetic_squad, matchday=1, use_modifier=True)
        self.assertEqual(len(res.starters), 11)
        self.assertGreater(res.total_expected_score, 0.0)

    def test_empty_strings_and_whitespace_items(self):
        """Input containing empty strings and pure whitespace items does not crash."""
        raw_input = "Svilar, ,   , Dimarco, Bremer, Bastoni, Buongiorno, Calhanoglu, Pulisic, Zaccagni, Nico Paz, Retegui, Martinez L., "
        res = self.optimizer.optimize_lineup(raw_input, matchday=1, use_modifier=True)
        self.assertEqual(len(res.starters), 11)

    def test_missing_or_none_fields_in_player_dict(self):
        """Player dicts with None values in mv, fm, xg, xa, piazzati, mod_rating."""
        squad = [
            {"nome": "Svilar", "ruolo": "P", "mv": None, "fm": None, "xg": None, "xa": None, "piazzati": None},
            {"nome": "Dimarco", "ruolo": "D", "mv": None, "fm": None, "xg": None, "xa": None},
            {"nome": "Bremer", "ruolo": "D", "mv": None, "fm": None},
            {"nome": "Bastoni", "ruolo": "D", "mv": None},
            {"nome": "Theo Hernandez", "ruolo": "D"},
            {"nome": "Calhanoglu", "ruolo": "C", "mv": None},
            {"nome": "Pulisic", "ruolo": "C"},
            {"nome": "Zaccagni", "ruolo": "C"},
            {"nome": "Nico Paz", "ruolo": "C"},
            {"nome": "Retegui", "ruolo": "A"},
            {"nome": "Martinez L.", "ruolo": "A"},
        ]
        res = self.optimizer.optimize_lineup(squad, matchday=1, use_modifier=True)
        self.assertEqual(len(res.starters), 11)
        for s in res.starters:
            self.assertGreater(s.expected_score, 0.0)
            self.assertGreater(s.expected_mv, 0.0)

    def test_empty_roster_raises_value_error(self):
        """Completely empty roster raises ValueError with clear message."""
        with self.assertRaises(ValueError):
            self.optimizer.optimize_lineup([])
        with self.assertRaises(ValueError):
            self.optimizer.optimize_lineup("")
        with self.assertRaises(ValueError):
            self.optimizer.optimize_lineup("   ,   ,   ")

    def test_json_and_csv_file_input_parsing(self):
        """Optimizer correctly accepts JSON and CSV file paths as roster input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p_json = Path(tmpdir) / "test_roster.json"
            p_csv = Path(tmpdir) / "test_roster.csv"

            squad_data = [
                {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.3},
                {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.5},
                {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.6},
                {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.4},
                {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.4},
                {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5},
                {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.5},
                {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.4},
                {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 6.5},
                {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.5},
                {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 6.6},
            ]

            with open(p_json, "w", encoding="utf-8") as f:
                json.dump(squad_data, f)
            res_json = self.optimizer.optimize_lineup(p_json)
            self.assertEqual(len(res_json.starters), 11)

            with open(p_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["nome", "squadra", "ruolo", "mv"])
                writer.writeheader()
                for p in squad_data:
                    writer.writerow(p)
            res_csv = self.optimizer.optimize_lineup(p_csv)
            self.assertEqual(len(res_csv.starters), 11)


# ==============================================================================
# 6. STRICT ZERO-TOLERANCE EXCLUSION OF INJURED & SUSPENDED PLAYERS
# ==============================================================================
class TestInjuredAndSuspendedExclusion(unittest.TestCase):
    """Stress tests verifying that no injured/suspended player ever starts or sits on bench."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_injured_superstar_with_astronomical_stats_is_never_fielded(self):
        """Even an injured player with 10.0 MV and 50.0 xG must be strictly excluded."""
        squad = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.0},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.0},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.0},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.0},
            {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.0},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.0},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.0},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.0},
            {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 6.0},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.0},
            {"nome": "Bonny", "squadra": "Parma", "ruolo": "A", "mv": 6.0},
            {
                "nome": "Superstar Injured Striker",
                "squadra": "Inter",
                "ruolo": "A",
                "mv": 10.0,
                "fm": 15.0,
                "xg": 50.0,
                "is_injured": True
            },
            {
                "nome": "Superstar Suspended Midfielder",
                "squadra": "Juventus",
                "ruolo": "C",
                "mv": 10.0,
                "fm": 15.0,
                "xg": 50.0,
                "is_suspended": True
            }
        ]
        res = self.optimizer.optimize_lineup(squad, matchday=1, use_modifier=True)
        starter_names = {s.nome for s in res.starters}
        bench_names = {b.nome for b in res.bench}
        excluded_names = {e.nome for e in res.excluded}

        self.assertNotIn("Superstar Injured Striker", starter_names)
        self.assertNotIn("Superstar Injured Striker", bench_names)
        self.assertIn("Superstar Injured Striker", excluded_names)

        self.assertNotIn("Superstar Suspended Midfielder", starter_names)
        self.assertNotIn("Superstar Suspended Midfielder", bench_names)
        self.assertIn("Superstar Suspended Midfielder", excluded_names)


# ==============================================================================
# 7. SCORE MONOTONICITY & TACTICAL OPTIMIZATION VERACITY
# ==============================================================================
class TestScoreMonotonicityAndTactics(unittest.TestCase):
    """Stress tests on score calculations, home/away advantages, and penalty kicks."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_penalty_taker_boost_on_expected_score(self):
        """Penalty takers receive a measurable bonus in expected score."""
        p_normal = {"nome": "Midfielder Regular", "squadra": "Serie A", "ruolo": "C", "mv": 6.0, "piazzati": ""}
        p_pen = {"nome": "Midfielder Rigorista", "squadra": "Serie A", "ruolo": "C", "mv": 6.0, "piazzati": "1° Rigorista"}

        ctx_normal = self.optimizer.build_player_match_context(p_normal, {}, [], matchday=1)
        ctx_pen = self.optimizer.build_player_match_context(p_pen, {}, [], matchday=1)

        self.assertGreater(ctx_pen.expected_score, ctx_normal.expected_score)


# ==============================================================================
# 8. CLI & JSON SERIALIZATION STRESS TESTING
# ==============================================================================
class TestCLIAdversarialExecution(unittest.TestCase):
    """Stress tests running best_lineup.py CLI subprocess with exotic arguments."""

    def test_cli_json_mode_schema_validation(self):
        """Verify CLI in --json mode returns 100% valid JSON matching FormationResult schema."""
        cmd = [
            sys.executable,
            str(WORKSPACE_ROOT / "best_lineup.py"),
            "--giornata", "1",
            "--modificatore",
            "--json"
        ]
        res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI execution failed: {res.stderr}")

        data = json.loads(res.stdout)
        self.assertIn("formation", data)
        self.assertIn(data["formation"], VALID_FORMATIONS)
        self.assertIn("total_expected_score", data)
        self.assertIn("starters_score", data)
        self.assertIn("modificatore_bonus", data)
        self.assertIn("defense_average", data)
        self.assertIn("tactical_rationale", data)
        self.assertIn("starters", data)
        self.assertEqual(len(data["starters"]), 11)
        self.assertIn("bench", data)
        self.assertIn("excluded", data)
        self.assertIn("formations_evaluated", data)

    def test_cli_no_modificatore_flag(self):
        """Verify CLI --no-modificatore sets bonus to 0."""
        cmd = [
            sys.executable,
            str(WORKSPACE_ROOT / "best_lineup.py"),
            "--no-modificatore",
            "--json"
        ]
        res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["modificatore_bonus"], 0.0)


# ==============================================================================
# 9. EMPIRICAL BUG REPRODUCTION TEST HARNESSES (FOR AUDIT EVIDENCE)
# ==============================================================================
class TestBugEvidenceHarnesses(unittest.TestCase):
    """Empirical demonstrations of confirmed vulnerabilities in best_lineup.py."""

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_reproduce_bug_adv_01_empty_team_code_home_away_reversal(self):
        """
        [BUG-ADV-01 Empirical Oracle]
        Demonstrates that when p_team_code is empty, p_team_code.upper() == fix.get('home_team_code', '').upper()
        evaluates '' == '', erroneously treating an away team player as playing at home.
        """
        p_away = {"nome": "Svilar", "squadra": "Roma", "squadra_code": "", "ruolo": "P", "mv": 6.3}
        fix_away = [{"home_team": "Inter", "home_team_code": "", "away_team": "Roma", "away_team_code": ""}]
        ctx = self.optimizer.build_player_match_context(p_away, {}, fix_away, matchday=1)
        # In flawed code, is_home is True due to '' == '' equality bug
        # This oracle records the exact observed failure
        is_bug_present = (ctx.is_home is True)
        self.assertTrue(is_bug_present, "BUG-ADV-01: Empty team code causes false positive home fixture")

    def test_reproduce_bug_adv_02_greedy_cross_club_role_overwrite(self):
        """
        [BUG-ADV-02 Empirical Oracle]
        Demonstrates that Dennis Man (Parma midfielder) gets matched against Mancini/Mangas
        from other clubs, overwriting his role from 'C' to 'D'.
        """
        p_man = {"nome": "Man", "squadra": "Parma", "ruolo": "C", "mv": 6.3}
        lineups = self.optimizer.load_matchday_lineups(1)
        ctx = self.optimizer.build_player_match_context(p_man, lineups, [], matchday=1)
        is_bug_present = (ctx.ruolo == "D")
        self.assertTrue(is_bug_present, "BUG-ADV-02: 'Man' role is overwritten to 'D' due to cross-club substring match")

    def test_reproduce_bug_adv_03_fallback_id_collision_drops_bench_players(self):
        """
        [BUG-ADV-03 Empirical Oracle]
        Demonstrates that multiple unlisted players with dummy id=9999 cause bench candidates
        to be dropped if one unlisted player starts.
        """
        squad = [
            {"nome": "Svilar", "ruolo": "P", "mv": 6.0},
            {"nome": "Dimarco", "ruolo": "D", "mv": 6.0},
            {"nome": "Bremer", "ruolo": "D", "mv": 6.0},
            {"nome": "Bastoni", "ruolo": "D", "mv": 6.0},
            {"nome": "Calhanoglu", "ruolo": "C", "mv": 6.0},
            {"nome": "Pulisic", "ruolo": "C", "mv": 6.0},
            {"nome": "Zaccagni", "ruolo": "C", "mv": 6.0},
            {"nome": "Nico Paz", "ruolo": "C", "mv": 6.0},
            {"nome": "Martinez L.", "ruolo": "A", "mv": 6.0},
            {"nome": "Retegui", "ruolo": "A", "mv": 6.0},
            {"nome": "Unlisted Starter", "ruolo": "A", "mv": 8.0},
            {"nome": "Unlisted Bench Player", "ruolo": "A", "mv": 5.0},
        ]
        res = self.optimizer.optimize_lineup(squad)
        bench_names = [b.nome for b in res.bench]
        is_bug_present = ("Unlisted Bench Player" not in bench_names)
        self.assertTrue(is_bug_present, "BUG-ADV-03: Unlisted bench candidate dropped due to id=9999 collision")

    def test_reproduce_bug_adv_04_missing_unicode_diacritics_normalization(self):
        """
        [BUG-ADV-04 Empirical Oracle]
        Demonstrates that normalize_name preserves diacritics instead of stripping them to ASCII,
        preventing matching between accented and unaccented variations.
        """
        norm_result = normalize_name("Çalhanoğlu")
        is_bug_present = (norm_result == "çalhanoğlu")
        self.assertTrue(is_bug_present, "BUG-ADV-04: normalize_name leaves Turkish/European diacritics unnormalized")


if __name__ == "__main__":
    unittest.main(verbosity=2)
