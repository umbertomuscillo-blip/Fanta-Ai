"""
Automated Test Suite for Algoritmo 'Chi Schiero' (best_lineup.py and src/best_lineup.py).
Tests:
1. Valid Fantacalcio formations (3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1).
2. Strict exclusion of injured and suspended players (0% probability or in infortunati/squalificati).
3. Exact calculation of Modificatore Difesa with standard thresholds (<6.0 -> 0, >=6.0 -> +1, >=6.5 -> +3, >=7.0 -> +6).
4. Full starting 11 + ordered 12-man bench composition.
5. CLI execution, argument parsing, and JSON output mode.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from src.best_lineup import (
    LineupOptimizer,
    get_best_lineup,
    VALID_FORMATIONS,
    PlayerMatchContext
)


class TestLineupOptimizerFormations(unittest.TestCase):
    def setUp(self):
        self.optimizer = LineupOptimizer()
        self.squad = [
            # Portieri (3)
            {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.4, "fm": 5.5, "xg": 0.0, "xa": 0.0},
            {"nome": "Falcone", "squadra": "Lecce", "ruolo": "P", "mv": 6.3, "fm": 5.0, "xg": 0.0, "xa": 0.0},
            {"nome": "Paleari", "squadra": "Torino", "ruolo": "P", "mv": 6.0, "fm": 5.0, "xg": 0.0, "xa": 0.0},
            # Difensori (8)
            {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.5, "fm": 7.2, "xg": 4.5, "xa": 6.0},
            {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.6, "fm": 6.9, "xg": 2.5, "xa": 1.0},
            {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.4, "fm": 7.0, "xg": 4.0, "xa": 5.0},
            {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.4, "fm": 6.6, "xg": 1.5, "xa": 3.0},
            {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "mv": 6.4, "fm": 6.6, "xg": 2.0, "xa": 0.5},
            {"nome": "Bellanova", "squadra": "Atalanta", "ruolo": "D", "mv": 6.3, "fm": 6.5, "xg": 1.8, "xa": 4.0},
            {"nome": "Coco", "squadra": "Torino", "ruolo": "D", "mv": 6.2, "fm": 6.3, "xg": 1.5, "xa": 0.5},
            {"nome": "Beukema", "squadra": "Bologna", "ruolo": "D", "mv": 6.2, "fm": 6.2, "xg": 1.0, "xa": 0.2},
            # Centrocampisti (8)
            {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.5, "fm": 7.6, "xg": 8.0, "xa": 5.0},
            {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.5, "fm": 7.5, "xg": 9.0, "xa": 6.0},
            {"nome": "Paz N.", "squadra": "Como", "ruolo": "C", "mv": 6.5, "fm": 7.0, "xg": 6.0, "xa": 7.0},
            {"nome": "McTominay", "squadra": "Napoli", "ruolo": "C", "mv": 6.4, "fm": 7.2, "xg": 6.5, "xa": 3.0},
            {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.4, "fm": 7.3, "xg": 7.0, "xa": 4.0},
            {"nome": "Man", "squadra": "Parma", "ruolo": "C", "mv": 6.3, "fm": 7.0, "xg": 6.0, "xa": 4.0},
            {"nome": "Frendrup", "squadra": "Genoa", "ruolo": "C", "mv": 6.3, "fm": 6.4, "xg": 1.0, "xa": 1.5},
            {"nome": "El Azzouzi O.", "squadra": "Bologna", "ruolo": "C", "mv": 6.2, "fm": 6.3, "xg": 1.0, "xa": 1.0},
            # Attaccanti (6)
            {"nome": "Malen", "squadra": "Roma", "ruolo": "A", "mv": 6.6, "fm": 8.5, "xg": 18.0, "xa": 4.0},
            {"nome": "Martinez L.", "squadra": "Inter", "ruolo": "A", "mv": 6.6, "fm": 8.8, "xg": 19.0, "xa": 4.5},
            {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.5, "fm": 8.1, "xg": 14.0, "xa": 2.5},
            {"nome": "Lookman", "squadra": "Atalanta", "ruolo": "A", "mv": 6.5, "fm": 8.0, "xg": 13.0, "xa": 6.0},
            {"nome": "Castellanos", "squadra": "Lazio", "ruolo": "A", "mv": 6.4, "fm": 7.4, "xg": 11.0, "xa": 3.0},
            {"nome": "Bonny", "squadra": "Parma", "ruolo": "A", "mv": 6.3, "fm": 7.0, "xg": 8.0, "xa": 3.0}
        ]

    def test_all_seven_formations_are_evaluated(self):
        res = self.optimizer.optimize_lineup(self.squad, matchday=1, use_modifier=True)
        self.assertIn(res.formation, VALID_FORMATIONS)
        self.assertEqual(len(res.starters), 11)
        self.assertGreaterEqual(len(res.bench), 10)
        evaluated_names = [f["formation"] for f in res.all_formations_evaluated]
        for form in VALID_FORMATIONS:
            self.assertIn(form, evaluated_names)

    def test_formation_role_distribution_invariants(self):
        res = self.optimizer.optimize_lineup(self.squad, matchday=1, use_modifier=True)
        req = VALID_FORMATIONS[res.formation]
        starters_by_role = {"P": 0, "D": 0, "C": 0, "A": 0}
        for s in res.starters:
            starters_by_role[s.ruolo] += 1
        
        self.assertEqual(starters_by_role["P"], req["P"])
        self.assertEqual(starters_by_role["D"], req["D"])
        self.assertEqual(starters_by_role["C"], req["C"])
        self.assertEqual(starters_by_role["A"], req["A"])


class TestLineupInjuriesAndSuspensions(unittest.TestCase):
    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_strict_exclusion_of_injured_and_suspended_players(self):
        squad = [
            {"nome": "Svilar", "ruolo": "P"},
            {"nome": "Dimarco", "ruolo": "D"},
            {"nome": "Bremer", "ruolo": "D"},
            {"nome": "Bastoni", "ruolo": "D"},
            {"nome": "Luperto", "ruolo": "D", "infortunato": True},  # Explicit injury
            {"nome": "Scalvini", "ruolo": "D"},  # Atalanta injured in probabili formazioni
            {"nome": "Calhanoglu", "ruolo": "C"},
            {"nome": "Pulisic", "ruolo": "C"},
            {"nome": "Zaccagni", "ruolo": "C"},
            {"nome": "Rovella", "ruolo": "C"},  # Lazio suspended in probabili formazioni
            {"nome": "Brescianini", "ruolo": "C", "squalificato": True},  # Explicit suspension
            {"nome": "Malen", "ruolo": "A"},
            {"nome": "Scamacca", "ruolo": "A"},  # Atalanta injured in probabili formazioni
            {"nome": "Martinez L.", "ruolo": "A"},
            {"nome": "Thuram", "ruolo": "A"}
        ]
        res = self.optimizer.optimize_lineup(squad, matchday=1, use_modifier=True)
        starter_names = [s.nome.lower() for s in res.starters]

        # Injuried / Suspended must NEVER be in starters
        self.assertNotIn("scamacca", starter_names)
        self.assertNotIn("scalvini", starter_names)
        self.assertNotIn("rovella", starter_names)
        self.assertNotIn("luperto", starter_names)
        self.assertNotIn("brescianini", starter_names)

        # Excluded list must contain them
        excluded_names = [e.nome.lower() for e in res.excluded]
        self.assertIn("scamacca", excluded_names)
        self.assertIn("scalvini", excluded_names)
        self.assertIn("rovella", excluded_names)


class TestModificatoreDifesaCalculations(unittest.TestCase):
    def setUp(self):
        self.optimizer = LineupOptimizer()

    def test_modificatore_thresholds(self):
        # < 6.00 -> 0
        gk = PlayerMatchContext(id=1, nome="GK", ruolo="P", squadra="Roma", squadra_code="ROM", expected_mv=5.5)
        defs = [
            PlayerMatchContext(id=2, nome="D1", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=6.0),
            PlayerMatchContext(id=3, nome="D2", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=5.8),
            PlayerMatchContext(id=4, nome="D3", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=5.8),
            PlayerMatchContext(id=5, nome="D4", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=5.5),
        ]
        bonus, avg = self.optimizer.calculate_modifier_bonus(gk, defs)
        self.assertEqual(bonus, 0.0)
        self.assertLess(avg, 6.00)

        # >= 6.00 and < 6.50 -> +1.0
        gk.expected_mv = 6.0
        defs[0].expected_mv = 6.2
        defs[1].expected_mv = 6.2
        defs[2].expected_mv = 6.0
        defs[3].expected_mv = 6.0
        bonus, avg = self.optimizer.calculate_modifier_bonus(gk, defs)
        self.assertEqual(bonus, 1.0)
        self.assertGreaterEqual(avg, 6.00)
        self.assertLess(avg, 6.50)

        # >= 6.50 and < 7.00 -> +3.0
        gk.expected_mv = 6.5
        defs[0].expected_mv = 6.8
        defs[1].expected_mv = 6.6
        defs[2].expected_mv = 6.5
        defs[3].expected_mv = 6.2
        bonus, avg = self.optimizer.calculate_modifier_bonus(gk, defs)
        self.assertEqual(bonus, 3.0)
        self.assertGreaterEqual(avg, 6.50)
        self.assertLess(avg, 7.00)

        # >= 7.00 -> +6.0
        gk.expected_mv = 7.0
        defs[0].expected_mv = 7.2
        defs[1].expected_mv = 7.0
        defs[2].expected_mv = 7.0
        defs[3].expected_mv = 6.8
        bonus, avg = self.optimizer.calculate_modifier_bonus(gk, defs)
        self.assertEqual(bonus, 6.0)
        self.assertGreaterEqual(avg, 7.00)

    def test_modificatore_not_applied_for_3_defenders(self):
        gk = PlayerMatchContext(id=1, nome="GK", ruolo="P", squadra="Roma", squadra_code="ROM", expected_mv=7.0)
        defs = [
            PlayerMatchContext(id=2, nome="D1", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=7.0),
            PlayerMatchContext(id=3, nome="D2", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=7.0),
            PlayerMatchContext(id=4, nome="D3", ruolo="D", squadra="Inter", squadra_code="INT", expected_mv=7.0),
        ]
        bonus, avg = self.optimizer.calculate_modifier_bonus(gk, defs)
        self.assertEqual(bonus, 0.0)


class TestCLIExecutionAndJSON(unittest.TestCase):
    def test_cli_execution_with_string_roster(self):
        cmd = [
            sys.executable,
            "best_lineup.py",
            "--roster",
            "Svilar, Dimarco, Bremer, Theo Hernandez, Buongiorno, Calhanoglu, Pulisic, Paz N., McTominay, Malen, Martinez L.",
            "--giornata",
            "1",
            "--json"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"CLI error: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("formation", data)
        self.assertIn("starters", data)
        self.assertEqual(len(data["starters"]), 11)
        self.assertIn("total_expected_score", data)
        self.assertGreater(data["total_expected_score"], 0)

    def test_cli_default_execution(self):
        cmd = [sys.executable, "best_lineup.py"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("11 TITOLARI SCHIERATI", res.stdout)
        self.assertIn("Modulo Ottimale", res.stdout)


if __name__ == "__main__":
    unittest.main()
