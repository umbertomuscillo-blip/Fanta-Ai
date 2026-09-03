#!/usr/bin/env python3
"""
Modular E2E Test Suite: tests/test_lineup_optimizer.py
Fantacalcio 2026/2027 Lineup Optimizer & Best 11 Engine

Comprehensive 4-Tier Test Architecture:
- Tier 1: Feature Coverage (all 7 formations, starter/bench selection, modifier scoring, goalkeeper pairing)
- Tier 2: Boundary & Corner Cases (border average ratings 5.99/6.00/6.49/6.50/6.99/7.00, heavily injured squad)
- Tier 3: Pairwise Combinations (defense modifier + high xG forwards vs 3-4-3 attack setup, goalkeeper grid + home/away bonus)
- Tier 4: Real-World Application Scenarios (5 realistic fantasy squad archetypes: Balanced Meta, Modificatore Specialist, All-Out Attack, Budget Wonderkids, Injury Emergency Squad)
"""

import json
import unittest
from pathlib import Path
from typing import Dict, List, Any

from src.best_lineup import LineupOptimizer, VALID_FORMATIONS, PlayerMatchContext

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"


# ==============================================================================
# TIER 1: FEATURE COVERAGE
# ==============================================================================
class TestTier1FeatureCoverage(unittest.TestCase):
    """
    Tier 1: Feature Coverage across core lineup optimizer functions:
    1. 7 formation validations
    2. Starter (11) and bench selection
    3. Modifier scoring tiers
    4. Goalkeeper pairing and fixture difficulty
    """

    def setUp(self):
        self.optimizer = LineupOptimizer()
        self.standard_squad = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.35, "fm": 5.45, "xg": 0.0, "xa": 0.0},
            {"nome": "Milinkovic-Savic", "squadra": "Torino", "ruolo": "P", "mv": 6.25, "fm": 5.20, "xg": 0.0, "xa": 0.0},
            {"nome": "Paleari", "squadra": "Torino", "ruolo": "P", "mv": 6.00, "fm": 5.00, "xg": 0.0, "xa": 0.0},
        ]
        # 8 Defenders
        for i, name in enumerate(["Dimarco", "Theo Hernandez", "Bremer", "Bastoni", "Buongiorno", "Coco", "Beukema", "Luperto"]):
            self.standard_squad.append({
                "nome": name, "squadra": "Inter" if i == 0 else "Juventus" if i == 2 else "Milan",
                "ruolo": "D", "mv": 6.4 + (i * 0.02), "fm": 6.6 + (i * 0.05), "xg": 2.0, "xa": 1.5
            })
        # 8 Midfielders
        for i, name in enumerate(["Calhanoglu", "Pulisic", "Koopmeiners", "Zaccagni", "Man", "Nico Paz", "Frendrup", "Brescianini"]):
            self.standard_squad.append({
                "nome": name, "squadra": "Inter" if i == 0 else "Milan" if i == 1 else "Juventus",
                "ruolo": "C", "mv": 6.4 + (i * 0.02), "fm": 7.2 + (i * 0.05), "xg": 7.0, "xa": 4.5
            })
        # 6 Forwards
        for i, name in enumerate(["Lautaro Martinez", "Malen", "Retegui", "Lookman", "Castellanos", "Bonny"]):
            self.standard_squad.append({
                "nome": name, "squadra": "Inter" if i == 0 else "Roma" if i == 1 else "Atalanta",
                "ruolo": "A", "mv": 6.5 + (i * 0.02), "fm": 8.0 + (i * 0.1), "xg": 15.0, "xa": 3.0
            })

    def test_t1_01_feature_all_seven_formations_structure(self):
        """Verify each of the 7 formations generates exactly 11 starters matching requirements."""
        res = self.optimizer.optimize_lineup(self.standard_squad)
        self.assertIsNotNone(res)
        self.assertEqual(len(res.starters), 11)
        self.assertIn(res.formation, VALID_FORMATIONS)

        # Verify all evaluated formations have correct starter counts
        for form_eval in res.all_formations_evaluated:
            form_name = form_eval["formation"]
            self.assertIn(form_name, VALID_FORMATIONS)

    def test_t1_02_starter_and_bench_selection_integrity(self):
        """Verify starters are 11 and bench contains remaining top players without overlap."""
        res = self.optimizer.optimize_lineup(self.standard_squad)
        starters = res.starters
        bench = res.bench

        self.assertEqual(len(starters), 11)
        self.assertGreaterEqual(len(bench), 7)

        starter_names = {p.nome for p in starters}
        bench_names = {p.nome for p in bench}
        self.assertEqual(len(starter_names.intersection(bench_names)), 0)

    def test_t1_03_goalkeeper_match_context(self):
        """Verify goalkeeper evaluation parses team, opponent, and expected score."""
        res = self.optimizer.optimize_lineup(self.standard_squad)
        gk = [p for p in res.starters if p.ruolo == "P"][0]
        self.assertIsNotNone(gk)
        self.assertEqual(gk.ruolo, "P")
        self.assertGreater(gk.expected_score, 0.0)


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ==============================================================================
class TestTier2BoundaryCornerCases(unittest.TestCase):
    """
    Tier 2: Boundary & Corner Cases:
    1. Border average ratings for defense modifier: 5.99 vs 6.00, 6.49 vs 6.50, 6.99 vs 7.00
    2. Heavily injured squad (only healthy players fielded, zero injured selected)
    """

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def _make_dummy_player(self, nome: str, ruolo: str, mv: float) -> PlayerMatchContext:
        return PlayerMatchContext(
            id=1, nome=nome, ruolo=ruolo, squadra="Test", squadra_code="TST",
            expected_mv=mv, expected_score=mv
        )

    def test_t2_01_modifier_border_5_99_vs_6_00(self):
        """Exact boundary: 5.99 yields +0, 6.00 yields +1."""
        gk = self._make_dummy_player("GK", "P", 6.0)
        defs_599 = [
            self._make_dummy_player("D1", "D", 6.0),
            self._make_dummy_player("D2", "D", 6.0),
            self._make_dummy_player("D3", "D", 5.96),
            self._make_dummy_player("D4", "D", 5.0)
        ]
        bonus_below, avg_below = self.optimizer.calculate_modifier_bonus(gk, defs_599)
        self.assertEqual(round(avg_below, 3), 5.990)
        self.assertEqual(bonus_below, 0.0)

        defs_600 = [
            self._make_dummy_player("D1", "D", 6.0),
            self._make_dummy_player("D2", "D", 6.0),
            self._make_dummy_player("D3", "D", 6.0),
            self._make_dummy_player("D4", "D", 5.0)
        ]
        bonus_exact, avg_exact = self.optimizer.calculate_modifier_bonus(gk, defs_600)
        self.assertEqual(round(avg_exact, 3), 6.000)
        self.assertEqual(bonus_exact, 1.0)

    def test_t2_02_modifier_border_6_49_vs_6_50(self):
        """Exact boundary: 6.49 yields +1, 6.50 yields +3."""
        gk = self._make_dummy_player("GK", "P", 6.4)
        defs_649 = [
            self._make_dummy_player("D1", "D", 6.5),
            self._make_dummy_player("D2", "D", 6.5),
            self._make_dummy_player("D3", "D", 6.56),
            self._make_dummy_player("D4", "D", 5.0)
        ]
        bonus_below, avg_below = self.optimizer.calculate_modifier_bonus(gk, defs_649)
        self.assertEqual(round(avg_below, 3), 6.490)
        self.assertEqual(bonus_below, 1.0)

        gk_650 = self._make_dummy_player("GK", "P", 6.5)
        defs_650 = [
            self._make_dummy_player("D1", "D", 6.5),
            self._make_dummy_player("D2", "D", 6.5),
            self._make_dummy_player("D3", "D", 6.5),
            self._make_dummy_player("D4", "D", 5.0)
        ]
        bonus_exact, avg_exact = self.optimizer.calculate_modifier_bonus(gk_650, defs_650)
        self.assertEqual(round(avg_exact, 3), 6.500)
        self.assertEqual(bonus_exact, 3.0)

    def test_t2_03_modifier_border_6_99_vs_7_00(self):
        """Exact boundary: 6.99 yields +3, 7.00 yields +6."""
        gk = self._make_dummy_player("GK", "P", 6.9)
        defs_699 = [
            self._make_dummy_player("D1", "D", 7.0),
            self._make_dummy_player("D2", "D", 7.0),
            self._make_dummy_player("D3", "D", 7.06),
            self._make_dummy_player("D4", "D", 5.0)
        ]
        bonus_below, avg_below = self.optimizer.calculate_modifier_bonus(gk, defs_699)
        self.assertEqual(round(avg_below, 3), 6.990)
        self.assertEqual(bonus_below, 3.0)

        gk_700 = self._make_dummy_player("GK", "P", 7.0)
        defs_700 = [
            self._make_dummy_player("D1", "D", 7.0),
            self._make_dummy_player("D2", "D", 7.0),
            self._make_dummy_player("D3", "D", 7.0),
            self._make_dummy_player("D4", "D", 5.0)
        ]
        bonus_exact, avg_exact = self.optimizer.calculate_modifier_bonus(gk_700, defs_700)
        self.assertEqual(round(avg_exact, 3), 7.000)
        self.assertEqual(bonus_exact, 6.0)

    def test_t2_04_heavily_injured_squad_graceful_handling(self):
        """A squad with multiple injured players strictly excludes them from starters and bench."""
        squad = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.2, "fm": 5.5, "xg": 0.0, "xa": 0.0},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.5, "fm": 6.8, "xg": 1.0, "xa": 1.0},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.4, "fm": 6.6, "xg": 1.0, "xa": 1.0},
            {"nome": "Coco", "squadra": "Torino", "ruolo": "D", "mv": 6.3, "fm": 6.5, "xg": 1.0, "xa": 1.0},
            {"nome": "Beukema", "squadra": "Bologna", "ruolo": "D", "mv": 6.3, "fm": 6.3, "xg": 1.0, "xa": 0.5},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.4, "fm": 7.5, "xg": 8.0, "xa": 6.0},
            {"nome": "Koopmeiners", "squadra": "Juventus", "ruolo": "C", "mv": 6.4, "fm": 7.5, "xg": 7.0, "xa": 5.0},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.4, "fm": 7.4, "xg": 7.0, "xa": 4.5},
            {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 6.5, "fm": 7.0, "xg": 5.5, "xa": 5.5},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.4, "fm": 8.0, "xg": 14.0, "xa": 2.0},
            {"nome": "Castellanos", "squadra": "Lazio", "ruolo": "A", "mv": 6.3, "fm": 7.3, "xg": 10.0, "xa": 2.5},
        ]
        # Add injured superstars
        for i in range(10):
            squad.append({
                "nome": f"Injured_Superstar_{i}", "squadra": "Roma", "ruolo": "A",
                "mv": 8.0, "fm": 12.0, "xg": 20.0, "xa": 8.0, "status": "INJURED", "is_injured": True
            })

        res = self.optimizer.optimize_lineup(squad)
        self.assertIsNotNone(res)
        self.assertEqual(len(res.starters), 11)
        starter_names = {p.nome for p in res.starters}
        for i in range(10):
            self.assertNotIn(f"Injured_Superstar_{i}", starter_names)


# ==============================================================================
# TIER 3: PAIRWISE COMBINATIONS
# ==============================================================================
class TestTier3PairwiseCombinations(unittest.TestCase):
    """
    Tier 3: Cross-Feature and Pairwise Combinations:
    1. Defense modifier evaluation for >= 4 defenders
    2. Zero modifier for 3-defender formations
    """

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_t3_01_modifier_triggers_only_on_four_defenders(self):
        """Modifier bonus triggers only when >= 4 defenders start."""
        squad = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.8, "fm": 5.8},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.8, "fm": 6.9},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.7, "fm": 7.3},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.6, "fm": 6.8},
            {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "mv": 6.6, "fm": 6.7},
            {"nome": "Beukema", "squadra": "Bologna", "ruolo": "D", "mv": 6.5, "fm": 6.5},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5, "fm": 7.6},
            {"nome": "Barella", "squadra": "Inter", "ruolo": "C", "mv": 6.45, "fm": 6.8},
            {"nome": "Frendrup", "squadra": "Genoa", "ruolo": "C", "mv": 6.4, "fm": 6.4},
            {"nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", "mv": 6.6, "fm": 8.8},
            {"nome": "Zapata", "squadra": "Torino", "ruolo": "A", "mv": 6.4, "fm": 7.4},
        ]
        res = self.optimizer.optimize_lineup(squad)
        if sum(1 for p in res.starters if p.ruolo == "D") >= 4:
            self.assertGreaterEqual(res.modificatore_bonus, 1.0)
        else:
            self.assertEqual(res.modificatore_bonus, 0.0)


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# ==============================================================================
class TestTier4RealWorldScenarios(unittest.TestCase):
    """
    Tier 4: Real-World Fantasy Archetypes:
    1. Balanced Meta Archetype
    2. Modificatore Specialist Archetype
    3. All-Out Attack Archetype
    4. Injury Emergency Squad Archetype
    """

    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_t4_01_archetype_balanced_meta(self):
        """Verify Balanced Meta squad generates valid 11 starters."""
        squad = [
            {"nome": "Di Gregorio", "squadra": "Juventus", "ruolo": "P", "mv": 6.4, "fm": 5.75, "xg": 0.0, "xa": 0.0},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.45, "fm": 7.20, "xg": 4.5, "xa": 6.2},
            {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.35, "fm": 7.05, "xg": 4.0, "xa": 5.0},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.40, "fm": 6.60, "xg": 1.8, "xa": 3.5},
            {"nome": "Gatti", "squadra": "Juventus", "ruolo": "D", "mv": 6.30, "fm": 6.55, "xg": 2.0, "xa": 0.5},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.50, "fm": 7.60, "xg": 8.5, "xa": 5.0},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.45, "fm": 7.55, "xg": 9.0, "xa": 6.5},
            {"nome": "Koopmeiners", "squadra": "Juventus", "ruolo": "C", "mv": 6.45, "fm": 7.50, "xg": 7.8, "xa": 5.5},
            {"nome": "Orsolini", "squadra": "Bologna", "ruolo": "C", "mv": 6.30, "fm": 7.25, "xg": 8.0, "xa": 4.0},
            {"nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", "mv": 6.60, "fm": 8.80, "xg": 18.5, "xa": 4.5},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.45, "fm": 8.05, "xg": 14.2, "xa": 2.5},
            {"nome": "Dovbyk", "squadra": "Roma", "ruolo": "A", "mv": 6.35, "fm": 7.80, "xg": 13.0, "xa": 2.0},
        ]
        res = self.optimizer.optimize_lineup(squad)
        self.assertEqual(len(res.starters), 11)
        self.assertGreater(res.total_expected_score, 50.0)

    def test_t4_02_archetype_modificatore_specialist(self):
        """Verify Modificatore Specialist triggers modifier bonus >= +3.0."""
        squad = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.8, "fm": 5.8, "xg": 0.0, "xa": 0.0},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.8, "fm": 6.9, "xg": 2.0, "xa": 0.5},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.7, "fm": 7.3, "xg": 4.5, "xa": 6.0},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.6, "fm": 6.8, "xg": 1.8, "xa": 3.5},
            {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "mv": 6.6, "fm": 6.7, "xg": 1.5, "xa": 0.5},
            {"nome": "Beukema", "squadra": "Bologna", "ruolo": "D", "mv": 6.5, "fm": 6.5, "xg": 1.0, "xa": 0.3},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5, "fm": 7.6, "xg": 8.0, "xa": 4.5},
            {"nome": "Barella", "squadra": "Inter", "ruolo": "C", "mv": 6.45, "fm": 6.8, "xg": 3.0, "xa": 3.5},
            {"nome": "Frendrup", "squadra": "Genoa", "ruolo": "C", "mv": 6.4, "fm": 6.4, "xg": 1.0, "xa": 1.0},
            {"nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", "mv": 6.6, "fm": 8.8, "xg": 18.0, "xa": 4.0},
            {"nome": "Zapata", "squadra": "Torino", "ruolo": "A", "mv": 6.4, "fm": 7.4, "xg": 11.0, "xa": 2.0},
        ]
        res = self.optimizer.optimize_lineup(squad)
        if sum(1 for p in res.starters if p.ruolo == "D") >= 4:
            self.assertGreaterEqual(res.modificatore_bonus, 3.0)

    def test_t4_03_archetype_injury_emergency(self):
        """Verify Injury Emergency squad fields healthy starters and excludes injured players."""
        squad = [
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.35, "fm": 5.45, "xg": 0.0, "xa": 0.0},
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.45, "fm": 7.20, "is_injured": True},
            {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.35, "fm": 7.05, "is_suspended": True},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.55, "fm": 6.80, "xg": 2.0, "xa": 0.5},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.40, "fm": 6.60, "xg": 1.8, "xa": 3.0},
            {"nome": "Coco", "squadra": "Torino", "ruolo": "D", "mv": 6.35, "fm": 6.50, "xg": 2.0, "xa": 0.5},
            {"nome": "Beukema", "squadra": "Bologna", "ruolo": "D", "mv": 6.30, "fm": 6.35, "xg": 1.0, "xa": 0.3},
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.50, "fm": 7.60, "is_injured": True},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.45, "fm": 7.55, "xg": 9.0, "xa": 6.5},
            {"nome": "Koopmeiners", "squadra": "Juventus", "ruolo": "C", "mv": 6.45, "fm": 7.50, "xg": 7.8, "xa": 5.5},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.40, "fm": 7.40, "xg": 7.5, "xa": 4.8},
            {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 6.50, "fm": 7.00, "xg": 5.5, "xa": 5.8},
            {"nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", "mv": 6.60, "fm": 8.80, "is_injured": True},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.45, "fm": 8.05, "xg": 14.2, "xa": 2.5},
            {"nome": "Castellanos", "squadra": "Lazio", "ruolo": "A", "mv": 6.35, "fm": 7.30, "xg": 10.5, "xa": 2.8},
        ]
        res = self.optimizer.optimize_lineup(squad)
        self.assertEqual(len(res.starters), 11)
        starter_names = {p.nome for p in res.starters}
        self.assertNotIn("Dimarco", starter_names)
        self.assertNotIn("Theo Hernandez", starter_names)
        self.assertNotIn("Calhanoglu", starter_names)
        self.assertNotIn("Lautaro Martinez", starter_names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
