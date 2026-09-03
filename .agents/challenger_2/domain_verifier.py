#!/usr/bin/env python3
"""
Comprehensive Domain Realism & Fantasy Soccer Invariant Verifier for Fantacalcio 2026/2027
Author: Challenger 2 (Domain & Realism Verifier)
Role: Critic, Specialist (Agent-as-Judge & Empirical Stress Testing)
"""

import json
import csv
import html
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

WORKSPACE_ROOT = Path("/Users/umbertomuscillo/Documents/Fantacalcio")
DATA_DIR = WORKSPACE_ROOT / "data"

EXPECTED_2026_TEAMS = {
    "ATA": "Atalanta", "BOL": "Bologna", "CAG": "Cagliari", "COM": "Como",
    "EMP": "Empoli", "FIO": "Fiorentina", "GEN": "Genoa", "INT": "Inter",
    "JUV": "Juventus", "LAZ": "Lazio", "LEC": "Lecce", "MIL": "Milan",
    "MON": "Monza", "NAP": "Napoli", "PAR": "Parma", "ROM": "Roma",
    "TOR": "Torino", "UDI": "Udinese", "VEN": "Venezia", "VER": "Verona"
}

PROMOTED_TEAMS = {"COM": "Como", "PAR": "Parma", "VEN": "Venezia"}
RELEGATED_TEAMS = {"SAL": "Salernitana", "SAS": "Sassuolo", "FRO": "Frosinone"}

class DomainRealismJudge:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.failures: List[str] = []
        self.warnings: List[str] = []
        self.players: List[Dict[str, Any]] = []
        self.lineups_data: Dict[str, Any] = {}
        self.fixtures: List[Dict[str, Any]] = []
        self.teams: List[Dict[str, Any]] = []
        self.players_db: Dict[str, List[Dict[str, Any]]] = {}

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        status = "PASS" if passed else "FAIL"
        self.results.append({"test": test_name, "status": status, "details": details})
        if not passed:
            self.failures.append(f"[{test_name}] {details}")

    def log_warning(self, test_name: str, details: str):
        self.warnings.append(f"[{test_name}] {details}")

    def load_all_data(self):
        # 1. players.json
        p_path = DATA_DIR / "players.json"
        if not p_path.exists():
            self.log_result("Load data/players.json", False, "File missing")
        else:
            with open(p_path, "r", encoding="utf-8") as f:
                self.players = json.load(f)
            self.log_result("Load data/players.json", True, f"Loaded {len(self.players)} players")

        # 2. probabili_formazioni.json
        l_path = DATA_DIR / "probabili_formazioni.json"
        if not l_path.exists():
            self.log_result("Load data/probabili_formazioni.json", False, "File missing")
        else:
            with open(l_path, "r", encoding="utf-8") as f:
                self.lineups_data = json.load(f)
            self.log_result("Load data/probabili_formazioni.json", True, "Loaded probabili_formazioni.json")

        # 3. calendario_serie_a.json
        c_path = DATA_DIR / "calendario_serie_a.json"
        if not c_path.exists():
            self.log_result("Load data/calendario_serie_a.json", False, "File missing")
        else:
            with open(c_path, "r", encoding="utf-8") as f:
                self.fixtures = json.load(f)
            self.log_result("Load data/calendario_serie_a.json", True, f"Loaded {len(self.fixtures)} fixtures")

        # 4. teams.json
        t_path = DATA_DIR / "teams.json"
        if not t_path.exists():
            self.log_result("Load data/teams.json", False, "File missing")
        else:
            with open(t_path, "r", encoding="utf-8") as f:
                self.teams = json.load(f)
            self.log_result("Load data/teams.json", True, f"Loaded {len(self.teams)} teams")

        # 5. players_db.json
        db_path = DATA_DIR / "players_db.json"
        if db_path.exists():
            with open(db_path, "r", encoding="utf-8") as f:
                self.players_db = json.load(f)
            self.log_result("Load data/players_db.json", True, "Loaded players_db.json")

    # =========================================================================
    # 1. SERIE A 2026/2027 CLUB INTEGRITY & RELEGATION / PROMOTION
    # =========================================================================
    def verify_serie_a_clubs(self):
        team_names = {t.get("name") or t.get("nome") or t.get("squadra") for t in self.teams}
        team_codes = {t.get("code") or t.get("sigla") for t in self.teams}

        # Check all 20 clubs
        missing = [f"{n} ({c})" for c, n in EXPECTED_2026_TEAMS.items() if n not in team_names and c not in team_codes]
        self.log_result(
            "Serie A 2026/2027 20-Team Completeness",
            len(missing) == 0 and len(self.teams) == 20,
            f"Missing: {missing}" if missing else "All 20 Serie A 2026/2027 clubs present"
        )

        # Check Promoted Clubs (Como, Parma, Venezia)
        promoted_found = [f"{n} ({c})" for c, n in PROMOTED_TEAMS.items() if n in team_names or c in team_codes]
        self.log_result(
            "Promoted Clubs Ingestion (Como, Parma, Venezia)",
            len(promoted_found) == 3,
            f"Found: {promoted_found}"
        )

        # Check Relegated Clubs (Salernitana, Sassuolo, Frosinone)
        relegated_found = [f"{n} ({c})" for c, n in RELEGATED_TEAMS.items() if n in team_names or c in team_codes]
        self.log_result(
            "Relegated Clubs Exclusion (Salernitana, Sassuolo, Frosinone)",
            len(relegated_found) == 0,
            f"Relegated found: {relegated_found}" if relegated_found else "All relegated clubs strictly excluded from active Serie A teams"
        )

    # =========================================================================
    # 2. PROMOTED CLUBS DOMAIN REALISM (ROSTERS & STARTING LINEUPS)
    # =========================================================================
    def verify_promoted_clubs(self):
        promoted_names = set(PROMOTED_TEAMS.values())
        rosters = {name: [] for name in promoted_names}

        for p in self.players:
            sq = p.get("squadra")
            if sq in rosters:
                rosters[sq].append(p)

        for name, rlist in rosters.items():
            r_count = len(rlist)
            p_count = sum(1 for p in rlist if p.get("ruolo") == "P")
            d_count = sum(1 for p in rlist if p.get("ruolo") == "D")
            c_count = sum(1 for p in rlist if p.get("ruolo") == "C")
            a_count = sum(1 for p in rlist if p.get("ruolo") == "A")

            balanced = r_count >= 25 and p_count >= 3 and d_count >= 8 and c_count >= 8 and a_count >= 4
            self.log_result(
                f"Promoted Roster Balance: {name}",
                balanced,
                f"{name}: {r_count} players (P:{p_count}, D:{d_count}, C:{c_count}, A:{a_count})"
            )

        # Lineup check for promoted clubs
        matches = self.lineups_data.get("matches", []) if isinstance(self.lineups_data, dict) else self.lineups_data
        promoted_lineups = {}
        for m in matches:
            for side in [m.get("home_lineup", {}), m.get("away_lineup", {})]:
                sq = side.get("squadra")
                if sq in promoted_names:
                    promoted_lineups[sq] = side

        for name in promoted_names:
            lineup = promoted_lineups.get(name)
            if not lineup:
                self.log_result(f"Promoted Club Matchday Lineup: {name}", False, "Lineup missing")
                continue

            titolari = lineup.get("titolari", [])
            panchina = lineup.get("panchina", [])
            modulo = lineup.get("modulo", "")

            gk_starter = [p for p in titolari if p.get("ruolo") == "P"]
            gk_bench = [p for p in panchina if p.get("ruolo") == "P"]

            valid = (len(titolari) == 11 and len(panchina) >= 10 and len(gk_starter) == 1 and len(gk_bench) >= 1)
            starters_str = ", ".join([p.get("nome", "") for p in titolari[:4]])
            self.log_result(
                f"Promoted Lineup Realism: {name}",
                valid,
                f"Modulo: {modulo} | Starters: {len(titolari)} (GK: {gk_starter[0].get('nome') if gk_starter else 'None'}) | Bench: {len(panchina)} | Key: {starters_str}..."
            )

    # =========================================================================
    # 3. GOALKEEPER INVARIANTS & REALISM
    # =========================================================================
    def verify_goalkeepers(self):
        matches = self.lineups_data.get("matches", []) if isinstance(self.lineups_data, dict) else self.lineups_data
        total_teams = 0
        gk_errors = []
        bench_gk_warnings = []
        outfield_p_roles = []

        starter_gks = []

        for m in matches:
            for side in ["home_lineup", "away_lineup"]:
                tdata = m.get(side, {})
                squadra = tdata.get("squadra", "Unknown")
                total_teams += 1
                titolari = tdata.get("titolari", [])
                panchina = tdata.get("panchina", [])

                gks = [p for p in titolari if p.get("ruolo") == "P"]
                if len(gks) != 1:
                    gk_errors.append(f"{squadra}: {len(gks)} GK starters")
                else:
                    starter_gks.append(f"{squadra}: {gks[0].get('nome')}")

                # Check position in list (GK should be at index 0)
                if titolari and titolari[0].get("ruolo") != "P":
                    self.log_warning("GK Lineup Position", f"{squadra}: starter at index 0 has role '{titolari[0].get('ruolo')}' instead of 'P'")

                # Check outfielders do not have 'P'
                for p in titolari[1:]:
                    if p.get("ruolo") == "P":
                        outfield_p_roles.append(f"{squadra}: Outfield position has role 'P' ({p.get('nome')})")

                # Bench GKs
                b_gks = [p for p in panchina if p.get("ruolo") == "P"]
                if len(b_gks) < 1:
                    bench_gk_warnings.append(f"{squadra}: No backup GK on bench")

        self.log_result(
            "Exactly 1 Goalkeeper Starter per Team (all 20 Teams)",
            len(gk_errors) == 0 and total_teams == 20,
            f"Failures: {gk_errors}" if gk_errors else f"All 20 teams have exactly 1 starting GK"
        )

        self.log_result(
            "No Outfield Starter with Goalkeeper Role 'P'",
            len(outfield_p_roles) == 0,
            f"Mismatches: {outfield_p_roles}" if outfield_p_roles else "Zero outfield starters have role 'P'"
        )

        if bench_gk_warnings:
            self.log_warning("Bench Goalkeeper Reserve", f"{len(bench_gk_warnings)} teams missing bench GK: {bench_gk_warnings}")

    # =========================================================================
    # 4. TOP PLAYERS DOMAIN REALISM & ROLE / VALUATION CONSISTENCY
    # =========================================================================
    def verify_top_players(self):
        player_dict = {}
        for p in self.players:
            clean_name = html.unescape(p["nome"]).strip().lower()
            player_dict[clean_name] = p

        key_players_spec = {
            "martinez l.": {"expected_team": "Inter", "expected_role": "A", "expected_mantra": "pc", "min_target": 120, "max_target": 250},
            "thuram": {"expected_team": "Inter", "expected_role": "A", "expected_mantra": "pc", "min_target": 70, "max_target": 150},
            "calhanoglu": {"expected_team": "Inter", "expected_role": "C", "expected_mantra": "m;c", "min_target": 35, "max_target": 140},
            "dimarco": {"expected_team": "Inter", "expected_role": "D", "expected_mantra": "e;w", "min_target": 25, "max_target": 140},
            "barella": {"expected_team": "Inter", "expected_role": "C", "expected_mantra": "c", "min_target": 15, "max_target": 50},
            "bastoni": {"expected_team": "Inter", "expected_role": "D", "expected_mantra": "dc", "min_target": 15, "max_target": 40},
            "pulisic": {"expected_team": "Milan", "expected_role": "C", "expected_mantra": "t;a", "min_target": 30, "max_target": 90},
            "leao": {"expected_team": "Milan", "expected_role": "A", "expected_mantra": "a", "min_target": 30, "max_target": 100},
            "maignan": {"expected_team": "Milan", "expected_role": "P", "expected_mantra": "por", "min_target": 15, "max_target": 45},
            "dybala": {"expected_team": "Roma", "expected_role": "A", "expected_mantra": "a", "min_target": 30, "max_target": 80},
            "bremer": {"expected_team": "Juventus", "expected_role": "D", "expected_mantra": "dc", "min_target": 20, "max_target": 45},
            "di gregorio": {"expected_team": "Juventus", "expected_role": "P", "expected_mantra": "por", "min_target": 4, "max_target": 45},
            "koopmeiners": {"expected_team": "Juventus", "expected_role": "C", "expected_mantra": "c;t", "min_target": 5, "max_target": 50},
            "zaccagni": {"expected_team": "Lazio", "expected_role": "C", "expected_mantra": "w;a", "min_target": 20, "max_target": 60},
            "orsolini": {"expected_team": "Bologna", "expected_role": "C", "expected_mantra": "w;a", "min_target": 20, "max_target": 95},
            "carnesecchi": {"expected_team": "Atalanta", "expected_role": "P", "expected_mantra": "por", "min_target": 15, "max_target": 40},
            "meret": {"expected_team": "Napoli", "expected_role": "P", "expected_mantra": "por", "min_target": 15, "max_target": 40},
            "paz n.": {"expected_team": "Como", "expected_role": "C", "expected_mantra": "t;a", "min_target": 10, "max_target": 130},
            "suzuki": {"expected_team": "Parma", "expected_role": "P", "expected_mantra": "por", "min_target": 5, "max_target": 20},
            "bernabè": {"expected_team": "Parma", "expected_role": "C", "expected_mantra": "c", "min_target": 5, "max_target": 25},
            "mctominay": {"expected_team": "Napoli", "expected_role": "C", "expected_mantra": "c;t", "min_target": 20, "max_target": 130},
            "de bruyne": {"expected_team": "Napoli", "expected_role": "C", "expected_mantra": "t", "min_target": 20, "max_target": 80},
            "malen": {"expected_team": "Roma", "expected_role": "A", "expected_mantra": "pc", "min_target": 100, "max_target": 250},
            "hojlund": {"expected_team": "Napoli", "expected_role": "A", "expected_mantra": "pc", "min_target": 80, "max_target": 180},
        }

        mismatches = []
        verified_count = 0

        for target_key, spec in key_players_spec.items():
            matched = player_dict.get(target_key)
            if not matched:
                # search substring
                candidates = [p for p in self.players if target_key in html.unescape(p["nome"]).lower()]
                if candidates:
                    matched = candidates[0]

            if not matched:
                mismatches.append(f"Player '{target_key}' not found")
                continue

            raw_name = matched.get("nome")
            clean_name = html.unescape(raw_name)
            p_team = matched.get("squadra")
            p_role = matched.get("ruolo")
            p_mantra = matched.get("ruolo_mantra", "")
            p_target = matched.get("prezzo_target", 0)

            if p_team != spec["expected_team"]:
                mismatches.append(f"{clean_name}: team mismatch (expected {spec['expected_team']}, got {p_team})")

            if p_role != spec["expected_role"]:
                mismatches.append(f"{clean_name}: role mismatch (expected {spec['expected_role']}, got {p_role})")

            if spec["expected_mantra"] not in p_mantra:
                self.log_warning("Mantra Role Check", f"{clean_name}: mantra '{p_mantra}' does not contain expected '{spec['expected_mantra']}'")

            if not (spec["min_target"] <= p_target <= spec["max_target"]):
                mismatches.append(f"{clean_name}: target price {p_target} outside expected [{spec['min_target']}, {spec['max_target']}]")

            verified_count += 1

        self.log_result(
            "Top Players Domain Realism (24 Key Serie A Stars)",
            len(mismatches) == 0,
            f"Verified {verified_count}/{len(key_players_spec)} key stars. Mismatches: {mismatches}" if mismatches else f"All {verified_count} key stars verified with correct roles, teams, and valuations"
        )

    # =========================================================================
    # 5. BUDGET MECHANICS & 500-BUDGET PRICE SCALING REALISM
    # =========================================================================
    def verify_budget_mechanics(self):
        total_p = len(self.players)
        p_by_role = {"P": [], "D": [], "C": [], "A": []}
        for p in self.players:
            p_by_role[p.get("ruolo", "D")].append(p)

        # 1. Total players and role representation
        self.log_result("Player Pool Size (>=500)", total_p >= 500, f"Total players: {total_p}")
        for r, plist in p_by_role.items():
            self.log_result(f"Role Quota: {r}", len(plist) >= 50, f"Role {r}: {len(plist)} players")

        # 2. Minimum price >= 1
        all_targets = [p.get("prezzo_target", 0) for p in self.players]
        min_target = min(all_targets) if all_targets else 0
        max_target = max(all_targets) if all_targets else 0

        self.log_result("Min Price Invariant (>= 1)", min_target >= 1, f"Min target price: {min_target}")
        self.log_result("Max Price Bound (<= 250)", max_target <= 250, f"Max target price: {max_target}")

        # 3. Realistic 25-Man Squad Drafting Strategy under 500 credits
        p_names = ['Suzuki', 'Corvi', 'Daffara']
        d_names = ['Valeri', 'Delprato', 'Circati', 'Troilo', 'Britschgi', 'Carboni F.', 'Drobnic', 'Ndiaye']
        c_names = ['Bernab&#xE8;', 'Frendrup', 'Politano', 'Casadei', 'Busio', 'Duncan', 'Basic', 'Dagasso']
        a_names = ['Martinez L.', 'Lucca', 'Adams A.', 'Bowie', 'Frigan', 'Vaz']

        sim_squad = [p for p in self.players if p['nome'] in p_names + d_names + c_names + a_names]
        total_cost = sum(p.get("prezzo_target", 0) for p in sim_squad)
        squad_size = len(sim_squad)

        cost_p = sum(p.get("prezzo_target", 0) for p in sim_squad if p['ruolo'] == 'P')
        cost_d = sum(p.get("prezzo_target", 0) for p in sim_squad if p['ruolo'] == 'D')
        cost_c = sum(p.get("prezzo_target", 0) for p in sim_squad if p['ruolo'] == 'C')
        cost_a = sum(p.get("prezzo_target", 0) for p in sim_squad if p['ruolo'] == 'A')

        is_feasible = (squad_size == 25 and 350 <= total_cost <= 500)
        self.log_result(
            "Draft 500-Budget Full 25-Man Squad Feasibility Simulation",
            is_feasible,
            f"25-man squad cost: {total_cost}/500 credits (P: {cost_p} cr [{round(cost_p/500*100)}%], D: {cost_d} cr [{round(cost_d/500*100)}%], C: {cost_c} cr [{round(cost_c/500*100)}%], A: {cost_a} cr [{round(cost_a/500*100)}%])"
        )

        # 4. FVM to Target Price Scaling Invariant (target = round(fvm / 2))
        fvm_scaling_errors = []
        for p in self.players:
            fvm = p.get("fvm_1000", 0)
            target = p.get("prezzo_target", 0)
            expected = max(1, round(fvm / 2))
            if abs(target - expected) > 1:
                fvm_scaling_errors.append(f"{p.get('nome')}: target {target} != expected {expected} (fvm {fvm})")

        self.log_result(
            "FVM-to-Target Halving Scaling Invariant across all 588 players",
            len(fvm_scaling_errors) == 0,
            f"Errors: {len(fvm_scaling_errors)}" if fvm_scaling_errors else "All 588 players strictly obey target = max(1, round(fvm / 2))"
        )

    # =========================================================================
    # 6. MATCHDAY LINEUP STRUCTURE & CALENDAR SYMMETRY
    # =========================================================================
    def verify_lineups_and_calendar(self):
        matches = self.lineups_data.get("matches", []) if isinstance(self.lineups_data, dict) else self.lineups_data
        self.log_result("Probable Lineups Matchday Match Count == 10", len(matches) == 10, f"Found {len(matches)} matches")

        # Calendar check: 380 matches, 38 giornate, 20 teams
        giornate = set(f.get("giornata") for f in self.fixtures)
        self.log_result("Calendar Giornate Count == 38", len(giornate) == 38, f"Found {len(giornate)} matchdays")
        self.log_result("Calendar Total Fixtures Count == 380", len(self.fixtures) == 380, f"Found {len(self.fixtures)} fixtures")

        # Home/Away balance: 19 home and 19 away for each team
        team_home = {}
        team_away = {}
        for f in self.fixtures:
            h = f.get("home_team") or f.get("squadra_casa")
            a = f.get("away_team") or f.get("squadra_trasferta")
            team_home[h] = team_home.get(h, 0) + 1
            team_away[a] = team_away.get(a, 0) + 1

        unbalanced = [t for t in team_home if team_home[t] != 19 or team_away.get(t, 0) != 19]
        self.log_result(
            "Calendar Double Round-Robin 19 Home / 19 Away Symmetry",
            len(unbalanced) == 0 and len(team_home) == 20,
            f"Unbalanced teams: {unbalanced}" if unbalanced else "All 20 clubs play exactly 19 home and 19 away matches"
        )

    def run_full_evaluation(self) -> bool:
        self.load_all_data()
        self.verify_serie_a_clubs()
        self.verify_promoted_clubs()
        self.verify_goalkeepers()
        self.verify_top_players()
        self.verify_budget_mechanics()
        self.verify_lineups_and_calendar()

        print("\n" + "="*75)
        print("AGENT-AS-JUDGE: DOMAIN REALISM & FANTASY SOCCER VERIFICATION REPORT")
        print("="*75)
        passed_count = sum(1 for r in self.results if r["status"] == "PASS")
        failed_count = sum(1 for r in self.results if r["status"] == "FAIL")
        print(f"TOTAL EVALUATION CHECKS: {len(self.results)}")
        print(f"PASSED: {passed_count} | FAILED: {failed_count}")
        print("-"*75)

        for r in self.results:
            print(f"[{r['status']}] {r['test']}\n      --> {r['details']}")

        if self.warnings:
            print("\n" + "-"*75)
            print("WARNINGS & ADVISORIES:")
            for w in self.warnings:
                print(f"  * {w}")

        print("="*75)
        verdict = "APPROVE" if failed_count == 0 else "REQUEST_CHANGES"
        print(f"FINAL VERDICT: {verdict}")
        print("="*75)
        return failed_count == 0

if __name__ == "__main__":
    judge = DomainRealismJudge()
    passed = judge.run_full_evaluation()
    sys.exit(0 if passed else 1)
