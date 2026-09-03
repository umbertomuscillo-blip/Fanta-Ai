"""
Algoritmo 'Chi Schiero' - Fantacalcio 2026/2027 Lineup Optimizer.
Crosses user roster with matchday lineups, injuries, suspensions, calendar fixtures,
goalkeeper grids, and computes optimal starting XI across all 7 official formations
with Modificatore Difesa evaluation and 12-man bench selection.
"""

import csv
import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple

from src.config import DATA_DIR
from src.goalkeeper_analyzer import ATTACK_TIER, DEFENSE_RATING

logger = logging.getLogger(__name__)

# Official 7 Fantacalcio Formations
VALID_FORMATIONS: Dict[str, Dict[str, int]] = {
    "3-4-3": {"P": 1, "D": 3, "C": 4, "A": 3},
    "3-5-2": {"P": 1, "D": 3, "C": 5, "A": 2},
    "4-3-3": {"P": 1, "D": 4, "C": 3, "A": 3},
    "4-4-2": {"P": 1, "D": 4, "C": 4, "A": 2},
    "4-5-1": {"P": 1, "D": 4, "C": 5, "A": 1},
    "5-3-2": {"P": 1, "D": 5, "C": 3, "A": 2},
    "5-4-1": {"P": 1, "D": 5, "C": 4, "A": 1},
}


@dataclass
class PlayerMatchContext:
    id: int
    nome: str
    ruolo: str
    squadra: str
    squadra_code: str
    opponent: str = ""
    opponent_code: str = ""
    is_home: bool = True
    fixture_difficulty: int = 2  # 1=Easy, 2=Medium, 3=Hard
    probabilita: int = 80
    status: str = "STARTER"  # STARTER, BENCH, INJURED, SUSPENDED, UNKNOWN
    ballottaggio_with: str = ""
    ballottaggio_pct: int = 0
    is_injured: bool = False
    is_suspended: bool = False
    injury_reason: str = ""
    mv: float = 6.0
    fm: float = 6.0
    xg: float = 0.0
    xa: float = 0.0
    piazzati: str = ""
    mod_rating: str = ""
    moneyball_index: float = 50.0
    expected_mv: float = 6.0
    expected_score: float = 6.0
    tactical_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FormationResult:
    formation: str
    starters: List[PlayerMatchContext]
    bench: List[PlayerMatchContext]
    excluded: List[PlayerMatchContext]
    starters_score: float
    modificatore_bonus: float
    defense_average: float
    total_expected_score: float
    tactical_rationale: str
    all_formations_evaluated: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "formation": self.formation,
            "total_expected_score": round(self.total_expected_score, 2),
            "starters_score": round(self.starters_score, 2),
            "modificatore_bonus": round(self.modificatore_bonus, 2),
            "defense_average": round(self.defense_average, 3),
            "tactical_rationale": self.tactical_rationale,
            "starters": [p.to_dict() for p in self.starters],
            "bench": [p.to_dict() for p in self.bench],
            "excluded": [p.to_dict() for p in self.excluded],
            "formations_evaluated": self.all_formations_evaluated
        }


def normalize_name(name: str) -> str:
    """Normalizes player name for robust fuzzy matching."""
    s = str(name).strip().lower()
    s = re.sub(r'[\.\,\'\"\-\_]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


class LineupOptimizer:
    def __init__(
        self,
        players_path: Optional[Union[str, Path]] = None,
        lineups_path: Optional[Union[str, Path]] = None,
        fixtures_path: Optional[Union[str, Path]] = None,
    ):
        self.players_path = Path(players_path) if players_path else (DATA_DIR / "players.json")
        self.lineups_path = Path(lineups_path) if lineups_path else (DATA_DIR / "probabili_formazioni.json")
        self.fixtures_path = Path(fixtures_path) if fixtures_path else (DATA_DIR / "calendario_serie_a.json")
        
        # Fallback aliases
        if not self.lineups_path.exists() and (DATA_DIR / "lineups.json").exists():
            self.lineups_path = DATA_DIR / "lineups.json"
        if not self.fixtures_path.exists() and (DATA_DIR / "calendar.json").exists():
            self.fixtures_path = DATA_DIR / "calendar.json"

        self.players_db: Dict[str, Dict[str, Any]] = {}
        self.raw_players_list: List[Dict[str, Any]] = []
        self._load_players_db()

    def _load_players_db(self) -> None:
        """Loads and indexes player database by multiple keys for fast resolution."""
        if not self.players_path.exists():
            logger.warning(f"Players DB not found at {self.players_path}")
            return

        with open(self.players_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            # Formatted by role P, D, C, A
            players = []
            for r in ["P", "D", "C", "A"]:
                players.extend(data.get(r, []))
            self.raw_players_list = players
        elif isinstance(data, list):
            self.raw_players_list = data
        else:
            self.raw_players_list = []

        for p in self.raw_players_list:
            name_raw = p.get("nome", "")
            norm = normalize_name(name_raw)
            self.players_db[norm] = p
            # Also index by single tokens if unique
            parts = norm.split()
            if len(parts) >= 2:
                # "martinez l" -> "martinez", "nico paz" -> "paz", "paz n" -> "paz"
                last_name = parts[0] if len(parts[1]) == 1 else parts[-1]
                if last_name not in self.players_db:
                    self.players_db[last_name] = p

    def match_player(self, raw_input: Union[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Matches a player name or dict to the database."""
        if isinstance(raw_input, dict):
            name = raw_input.get("nome") or raw_input.get("name") or raw_input.get("player") or ""
            role = raw_input.get("ruolo") or raw_input.get("role") or ""
        else:
            name = str(raw_input).strip()
            role = ""

        if not name:
            return None

        norm = normalize_name(name)
        if norm in self.players_db:
            p = dict(self.players_db[norm])
            if isinstance(raw_input, dict):
                p.update(raw_input)
            if role and not p.get("ruolo"):
                p["ruolo"] = role.upper()
            return p

        # Check partial/contains matching
        for k, p in self.players_db.items():
            if norm == k or norm in k or k in norm:
                res = dict(p)
                if isinstance(raw_input, dict):
                    res.update(raw_input)
                if role and not res.get("ruolo"):
                    res["ruolo"] = role.upper()
                return res

        # Fallback dummy record with reasonable defaults if player not found
        guessed_role = role.upper() if role in {"P", "D", "C", "A"} else "C"
        return {
            "id": 9999,
            "nome": name,
            "squadra": "Serie A",
            "squadra_code": "SA",
            "ruolo": guessed_role,
            "mv": 6.0,
            "fm": 6.0,
            "xg": 0.1,
            "xa": 0.1,
            "piazzati": "",
            "mod_rating": "",
            "moneyball_index": 50.0
        }

    def parse_roster(self, roster_input: Union[str, Path, List[Any], Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parses any input format (JSON file, CSV file, comma string, list, dict)."""
        raw_list: List[Any] = []

        if isinstance(roster_input, (str, Path)):
            s = str(roster_input).strip()
            p = Path(s)
            if p.exists() and p.is_file():
                if p.suffix.lower() == ".json":
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            raw_list = data
                        elif isinstance(data, dict):
                            for r in ["P", "D", "C", "A"]:
                                if r in data and isinstance(data[r], list):
                                    raw_list.extend(data[r])
                                elif r.lower() in data and isinstance(data[r.lower()], list):
                                    raw_list.extend(data[r.lower()])
                            if not raw_list and "roster" in data:
                                raw_list = data["roster"]
                            elif not raw_list and "players" in data:
                                raw_list = data["players"]
                elif p.suffix.lower() == ".csv":
                    with open(p, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        raw_list = list(reader)
                else:
                    # Treat text file lines as player names
                    with open(p, "r", encoding="utf-8") as f:
                        raw_list = [line.strip() for line in f if line.strip()]
            else:
                # String input: check if JSON string or comma-separated
                if s.startswith("[") or s.startswith("{"):
                    try:
                        data = json.loads(s)
                        if isinstance(data, list):
                            raw_list = data
                        elif isinstance(data, dict):
                            for r in ["P", "D", "C", "A"]:
                                if r in data:
                                    raw_list.extend(data[r])
                            if not raw_list and "players" in data:
                                raw_list = data["players"]
                    except Exception:
                        raw_list = [item.strip() for item in s.split(",") if item.strip()]
                else:
                    # Comma or newline separated
                    delim = "\n" if "\n" in s else ","
                    raw_list = [item.strip() for item in s.split(delim) if item.strip()]

        elif isinstance(roster_input, list):
            raw_list = roster_input
        elif isinstance(roster_input, dict):
            for r in ["P", "D", "C", "A"]:
                if r in roster_input:
                    raw_list.extend(roster_input[r])
            if not raw_list and "players" in roster_input:
                raw_list = roster_input["players"]

        parsed_players: List[Dict[str, Any]] = []
        seen_names = set()

        for item in raw_list:
            matched = self.match_player(item)
            if matched:
                key = matched.get("nome", "").lower()
                if key not in seen_names:
                    seen_names.add(key)
                    parsed_players.append(matched)

        return parsed_players

    def load_matchday_lineups(self, matchday: int = 1) -> Dict[str, Any]:
        """Loads probabili formazioni for the specified matchday."""
        if not self.lineups_path.exists():
            logger.warning(f"Lineups file {self.lineups_path} not found.")
            return {}

        with open(self.lineups_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def load_matchday_fixtures(self, matchday: int = 1) -> List[Dict[str, Any]]:
        """Loads fixtures for the specified matchday."""
        if not self.fixtures_path.exists():
            return []

        with open(self.fixtures_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = []
        raw_fixtures = data if isinstance(data, list) else data.get("matches", [])
        for m in raw_fixtures:
            if m.get("giornata") == matchday:
                matches.append(m)
        return matches

    def build_player_match_context(
        self,
        player_dict: Dict[str, Any],
        lineups_data: Dict[str, Any],
        fixtures: List[Dict[str, Any]],
        matchday: int = 1
    ) -> PlayerMatchContext:
        """
        Builds full match context for a player, crossing with probable lineups,
        injuries, suspensions, ballotaggi, and fixture difficulty.
        """
        p_name = player_dict.get("nome", "")
        p_role = player_dict.get("ruolo", "C").upper()
        p_team = player_dict.get("squadra", "")
        p_team_code = player_dict.get("squadra_code", "")
        p_mv = float(player_dict.get("mv") or 6.0)
        p_fm = float(player_dict.get("fm") or 6.0)
        p_xg = float(player_dict.get("xg") or 0.0)
        p_xa = float(player_dict.get("xa") or 0.0)
        p_piazzati = player_dict.get("piazzati", "")
        p_mod = player_dict.get("mod_rating", "")
        p_moneyball = float(player_dict.get("moneyball_index") or 50.0)

        # Default fixture info
        opponent = "Serie A"
        opponent_code = "SA"
        is_home = True
        fixture_difficulty = 2

        # 1. Cross with fixtures
        for fix in fixtures:
            h_team = fix.get("home_team", "")
            a_team = fix.get("away_team", "")
            if p_team.lower() == h_team.lower() or p_team_code.upper() == fix.get("home_team_code", "").upper():
                is_home = True
                opponent = a_team
                opponent_code = fix.get("away_team_code", "")
                diff_map = fix.get("difficolta_portieri", {})
                fixture_difficulty = diff_map.get(p_team, 1 if ATTACK_TIER.get(opponent, 3) >= 3 else 2)
                break
            elif p_team.lower() == a_team.lower() or p_team_code.upper() == fix.get("away_team_code", "").upper():
                is_home = False
                opponent = h_team
                opponent_code = fix.get("home_team_code", "")
                diff_map = fix.get("difficolta_portieri", {})
                fixture_difficulty = diff_map.get(p_team, 3 if ATTACK_TIER.get(opponent, 2) <= 2 else 2)
                break

        # 2. Cross with probabili formazioni & explicit roster flags
        is_injured = bool(player_dict.get("is_injured") or player_dict.get("infortunato") or str(player_dict.get("status", "")).upper() in {"INJURED", "INFORTUNATO"})
        is_suspended = bool(player_dict.get("is_suspended") or player_dict.get("squalificato") or str(player_dict.get("status", "")).upper() in {"SUSPENDED", "SQUALIFICATO"})
        status = "INJURED" if is_injured else "SUSPENDED" if is_suspended else "STARTER"
        probability = 0 if (is_injured or is_suspended) else 85
        injury_reason = "Infortunato" if is_injured else "Squalificato" if is_suspended else ""
        ballottaggio_with = ""
        ballottaggio_pct = 0

        p_norm = normalize_name(p_name)
        matches_lineups = lineups_data.get("matches", [])

        for ml in matches_lineups:
            for t_lineup in [ml.get("home_lineup"), ml.get("away_lineup")]:
                if not t_lineup:
                    continue

                # Check infortunati
                for inj in t_lineup.get("infortunati", []):
                    inj_name = inj if isinstance(inj, str) else inj.get("nome", "")
                    if normalize_name(inj_name) in p_norm or p_norm in normalize_name(inj_name):
                        is_injured = True
                        status = "INJURED"
                        probability = 0
                        injury_reason = inj.get("motivo", "Infortunato") if isinstance(inj, dict) else "Infortunato"
                        break

                # Check squalificati
                for squ in t_lineup.get("squalificati", []):
                    squ_name = squ if isinstance(squ, str) else squ.get("nome", "")
                    if normalize_name(squ_name) in p_norm or p_norm in normalize_name(squ_name):
                        is_suspended = True
                        status = "SUSPENDED"
                        probability = 0
                        injury_reason = "Squalificato"
                        break

                if is_injured or is_suspended:
                    break

                # Check titolari
                for tit in t_lineup.get("titolari", []):
                    tit_name = tit.get("nome", "")
                    if normalize_name(tit_name) == p_norm or p_norm in normalize_name(tit_name) or normalize_name(tit_name) in p_norm:
                        status = "STARTER"
                        probability = tit.get("probabilita", 90)
                        if p_role == "C" and tit.get("ruolo") in {"P", "D", "C", "A"}:
                            p_role = tit.get("ruolo")
                        break

                # Check panchina
                for pan in t_lineup.get("panchina", []):
                    pan_name = pan.get("nome", "")
                    if normalize_name(pan_name) == p_norm or p_norm in normalize_name(pan_name) or normalize_name(pan_name) in p_norm:
                        status = "BENCH"
                        probability = pan.get("probabilita", 35)
                        break

                # Check ballottaggi
                for bal in t_lineup.get("ballottaggi", []):
                    b_tit = bal.get("titolare", "")
                    b_sub = bal.get("sostituto", "")
                    if normalize_name(b_tit) in p_norm or p_norm in normalize_name(b_tit):
                        ballottaggio_with = b_sub
                        ballottaggio_pct = bal.get("percentuale", 55)
                        probability = ballottaggio_pct
                    elif normalize_name(b_sub) in p_norm or p_norm in normalize_name(b_sub):
                        ballottaggio_with = b_tit
                        ballottaggio_pct = 100 - bal.get("percentuale", 55)
                        probability = ballottaggio_pct

            if is_injured or is_suspended:
                break

        # 3. Compute Expected Media Voto (MV) and Expected Total Score
        if is_injured or is_suspended or probability <= 0:
            expected_mv = 0.0
            expected_score = 0.0
            tactical_note = f"NON SCHIERABILE: {injury_reason}"
        else:
            # Base expected MV
            base_mv = max(5.8, p_mv if p_mv > 0 else 6.0)
            
            # Fixture difficulty adjustment on MV
            if fixture_difficulty == 1:
                fixture_mv_adj = +0.25 if is_home else +0.10
            elif fixture_difficulty == 3:
                fixture_mv_adj = -0.25 if not is_home else -0.10
            else:
                fixture_mv_adj = +0.05 if is_home else -0.05

            mod_boost = 0.20 if (p_mod in {"A+", "A", "TOP"}) else 0.0
            expected_mv = round(min(7.5, max(5.0, base_mv + fixture_mv_adj + mod_boost)), 2)

            # Bonus expectations
            prob_factor = (probability / 100.0)
            # Starter bonus vs Bench discount
            if status == "STARTER":
                starter_mult = 1.0 if probability >= 80 else 0.90
            else:
                starter_mult = 0.55 if probability >= 40 else 0.35

            if p_role == "P":
                # Goalkeeper score: MV + clean sheet bonus - expected goals conceded
                def_solid = DEFENSE_RATING.get(p_team, 6.5)
                opp_att = ATTACK_TIER.get(opponent, 3)
                exp_conceded = max(0.2, round((5 - opp_att) * 0.45 - (def_solid - 6.0) * 0.15 + (0.3 if not is_home else 0.0), 2))
                clean_sheet_chance = max(0.1, round(0.55 - (5 - opp_att) * 0.10 + (def_solid - 6.0) * 0.08 + (0.1 if is_home else 0.0), 2))
                expected_score = round(((expected_mv - exp_conceded + clean_sheet_chance) * prob_factor * starter_mult), 2)
            elif p_role == "D":
                # Defender score: MV + xG/xA bonus
                match_xg = (p_xg / 34.0) if p_xg > 0 else 0.03
                match_xa = (p_xa / 34.0) if p_xa > 0 else 0.04
                bonus = (match_xg * 3.0) + (match_xa * 1.0)
                expected_score = round(((expected_mv + bonus) * prob_factor * starter_mult), 2)
            elif p_role == "C":
                # Midfielder score: MV + xG/xA bonus + penalty boost
                match_xg = (p_xg / 34.0) if p_xg > 0 else 0.08
                match_xa = (p_xa / 34.0) if p_xa > 0 else 0.10
                pen_bonus = 0.30 if "Rigorista" in p_piazzati else 0.0
                bonus = (match_xg * 3.0) + (match_xa * 1.0) + pen_bonus
                expected_score = round(((expected_mv + bonus) * prob_factor * starter_mult), 2)
            else:
                # Attacker score: MV + heavy goal bonus
                match_xg = (p_xg / 34.0) if p_xg > 0 else 0.35
                match_xa = (p_xa / 34.0) if p_xa > 0 else 0.10
                pen_bonus = 0.40 if "Rigorista" in p_piazzati else 0.0
                bonus = (match_xg * 3.0) + (match_xa * 1.0) + pen_bonus
                expected_score = round(((expected_mv + bonus) * prob_factor * starter_mult), 2)

            # Generate insightful tactical note
            home_str = "Casa" if is_home else "Trasferta"
            diff_str = "Facile" if fixture_difficulty == 1 else "Media" if fixture_difficulty == 2 else "Difficile"
            parts = [f"{p_team} vs {opponent} ({home_str}, {diff_str})"]
            if status == "STARTER":
                parts.append(f"Titolare {probability}%")
            else:
                parts.append(f"Panchina {probability}%")
            if ballottaggio_with:
                parts.append(f"Ballottaggio con {ballottaggio_with}")
            if p_piazzati:
                parts.append(p_piazzati)
            if p_mod:
                parts.append(f"Mod {p_mod}")
            tactical_note = " • ".join(parts)

        return PlayerMatchContext(
            id=player_dict.get("id", 0),
            nome=p_name,
            ruolo=p_role,
            squadra=p_team,
            squadra_code=p_team_code,
            opponent=opponent,
            opponent_code=opponent_code,
            is_home=is_home,
            fixture_difficulty=fixture_difficulty,
            probabilita=probability,
            status=status,
            ballottaggio_with=ballottaggio_with,
            ballottaggio_pct=ballottaggio_pct,
            is_injured=is_injured,
            is_suspended=is_suspended,
            injury_reason=injury_reason,
            mv=p_mv,
            fm=p_fm,
            xg=p_xg,
            xa=p_xa,
            piazzati=p_piazzati,
            mod_rating=p_mod,
            moneyball_index=p_moneyball,
            expected_mv=expected_mv,
            expected_score=expected_score,
            tactical_note=tactical_note
        )

    def calculate_modifier_bonus(self, gk: PlayerMatchContext, defenders: List[PlayerMatchContext]) -> Tuple[float, float]:
        """
        Computes Modificatore Difesa for $\ge 4$ defenders:
        Average of GK expected MV + Top 3 Defenders expected MV.
        Bonus brackets:
        < 6.00 -> 0.0
        >= 6.00 and < 6.50 -> +1.0
        >= 6.50 and < 7.00 -> +3.0
        >= 7.00 -> +6.0
        """
        if len(defenders) < 4:
            return 0.0, 0.0

        sorted_defs = sorted(defenders, key=lambda d: d.expected_mv, reverse=True)
        top3_defs = sorted_defs[:3]
        avg = (gk.expected_mv + top3_defs[0].expected_mv + top3_defs[1].expected_mv + top3_defs[2].expected_mv) / 4.0

        if avg >= 7.00:
            bonus = 6.0
        elif avg >= 6.50:
            bonus = 3.0
        elif avg >= 6.00:
            bonus = 1.0
        else:
            bonus = 0.0

        return bonus, avg

    def optimize_lineup(
        self,
        roster_input: Union[str, Path, List[Any], Dict[str, Any]],
        matchday: int = 1,
        use_modifier: bool = True
    ) -> FormationResult:
        """
        Main optimization algorithm:
        1. Parses user roster.
        2. Crosses with probabili formazioni & calendar.
        3. Strictly excludes injured / suspended players.
        4. Evaluates all 7 official formations.
        5. Computes defense modifier where applicable.
        6. Selects optimal formation, 11 starters, and 12-man ordered bench.
        """
        raw_players = self.parse_roster(roster_input)
        if not raw_players:
            raise ValueError("No valid players found in provided roster.")

        lineups_data = self.load_matchday_lineups(matchday)
        fixtures = self.load_matchday_fixtures(matchday)

        contexts: List[PlayerMatchContext] = [
            self.build_player_match_context(p, lineups_data, fixtures, matchday)
            for p in raw_players
        ]

        # Separate available from strictly excluded (injured/suspended)
        available_by_role: Dict[str, List[PlayerMatchContext]] = {"P": [], "D": [], "C": [], "A": []}
        excluded_players: List[PlayerMatchContext] = []

        for ctx in contexts:
            if ctx.is_injured or ctx.is_suspended or ctx.probabilita <= 0:
                excluded_players.append(ctx)
            else:
                r = ctx.ruolo if ctx.ruolo in available_by_role else "C"
                available_by_role[r].append(ctx)

        # Sort available players by expected_score descending
        for r in available_by_role:
            available_by_role[r].sort(key=lambda x: x.expected_score, reverse=True)

        # Evaluate all 7 formations
        formations_eval: List[Dict[str, Any]] = []
        best_formation_name = ""
        best_total_score = -1.0
        best_starters: List[PlayerMatchContext] = []
        best_mod_bonus = 0.0
        best_def_avg = 0.0

        for form_name, req in VALID_FORMATIONS.items():
            req_p = req["P"]
            req_d = req["D"]
            req_c = req["C"]
            req_a = req["A"]

            # Check eligibility
            if (len(available_by_role["P"]) < req_p or
                len(available_by_role["D"]) < req_d or
                len(available_by_role["C"]) < req_c or
                len(available_by_role["A"]) < req_a):
                formations_eval.append({
                    "formation": form_name,
                    "eligible": False,
                    "reason": "Giocatori disponibili insufficienti per questo modulo",
                    "total_score": 0.0,
                    "mod_bonus": 0.0,
                    "def_avg": 0.0
                })
                continue

            picked_p = available_by_role["P"][:req_p]
            picked_d = available_by_role["D"][:req_d]
            picked_c = available_by_role["C"][:req_c]
            picked_a = available_by_role["A"][:req_a]

            starters = picked_p + picked_d + picked_c + picked_a
            starters_score = sum(s.expected_score for s in starters)

            mod_bonus = 0.0
            def_avg = 0.0
            if use_modifier and req_d >= 4 and picked_p and len(picked_d) >= 4:
                mod_bonus, def_avg = self.calculate_modifier_bonus(picked_p[0], picked_d)

            total_score = starters_score + mod_bonus

            formations_eval.append({
                "formation": form_name,
                "eligible": True,
                "starters_score": round(starters_score, 2),
                "mod_bonus": round(mod_bonus, 2),
                "def_avg": round(def_avg, 3),
                "total_score": round(total_score, 2)
            })

            if total_score > best_total_score:
                best_total_score = total_score
                best_formation_name = form_name
                best_starters = starters
                best_mod_bonus = mod_bonus
                best_def_avg = def_avg

        # If no strict formation met requirements due to small roster, take top 11 available
        if not best_starters:
            all_avail = sorted(
                [p for r in available_by_role.values() for p in r],
                key=lambda x: x.expected_score,
                reverse=True
            )
            best_starters = all_avail[:11]
            best_formation_name = "3-5-2"
            best_total_score = sum(s.expected_score for s in best_starters)
            best_mod_bonus = 0.0
            best_def_avg = 0.0

        # Build Bench (12 players ordered by role: P, D, C, A and expected score)
        starters_ids = {s.id for s in best_starters}
        bench_candidates = [ctx for ctx in contexts if ctx.id not in starters_ids and ctx not in excluded_players]

        bench_p = [p for p in bench_candidates if p.ruolo == "P"]
        bench_d = [p for p in bench_candidates if p.ruolo == "D"]
        bench_c = [p for p in bench_candidates if p.ruolo == "C"]
        bench_a = [p for p in bench_candidates if p.ruolo == "A"]

        bench_p.sort(key=lambda x: x.expected_score, reverse=True)
        bench_d.sort(key=lambda x: x.expected_score, reverse=True)
        bench_c.sort(key=lambda x: x.expected_score, reverse=True)
        bench_a.sort(key=lambda x: x.expected_score, reverse=True)

        ordered_bench = bench_p + bench_d + bench_c + bench_a
        # Cap bench at 12 players standard
        final_bench = ordered_bench[:12]

        # Generate Tactical Rationale
        req_d_count = VALID_FORMATIONS.get(best_formation_name, {}).get("D", 3)
        mod_text = ""
        if use_modifier and req_d_count >= 4:
            if best_mod_bonus > 0:
                mod_text = f" e attiva con successo il Modificatore Difesa (Media Difesa {best_def_avg:.2f} -> Bonus +{best_mod_bonus:.1f} pt)"
            else:
                mod_text = f" (Modificatore Difesa non attivo: Media Difesa {best_def_avg:.2f} < 6.00)"

        tactical_rationale = (
            f"Modulo ottimale {best_formation_name} con punteggio previsto di {best_total_score:.2f} pt. "
            f"La formazione massimizza l'efficacia offensiva dei titolari a disposizione{mod_text}. "
            f"Esclusi {len(excluded_players)} calciatori indisponibili per infortunio/squalifica."
        )

        return FormationResult(
            formation=best_formation_name,
            starters=best_starters,
            bench=final_bench,
            excluded=excluded_players,
            starters_score=round(sum(s.expected_score for s in best_starters), 2),
            modificatore_bonus=best_mod_bonus,
            defense_average=best_def_avg,
            total_expected_score=round(best_total_score, 2),
            tactical_rationale=tactical_rationale,
            all_formations_evaluated=formations_eval
        )


def get_best_lineup(
    roster: Union[str, Path, List[Any], Dict[str, Any]],
    lineups_path: Optional[Union[str, Path]] = None,
    fixtures_path: Optional[Union[str, Path]] = None,
    players_path: Optional[Union[str, Path]] = None,
    matchday: int = 1,
    use_modifier: bool = True
) -> FormationResult:
    """Convenience functional API to optimize a lineup."""
    optimizer = LineupOptimizer(
        players_path=players_path,
        lineups_path=lineups_path,
        fixtures_path=fixtures_path
    )
    return optimizer.optimize_lineup(roster, matchday=matchday, use_modifier=use_modifier)
