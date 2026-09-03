"""
Validator for Serie A 2026/2027 season compliance and data integrity.
Enforces 20 active Serie A teams (including Como, Parma, Venezia),
strictly prohibits relegated teams (Salernitana, Sassuolo, Frosinone),
and verifies domain integrity invariants.
"""

import logging
from typing import List, Dict, Any, Set

from src.config import (
    SERIE_A_TEAMS_2026_2027,
    PROMOTED_TEAMS_2026_2027,
    RELEGATED_TEAMS
)
from src.models import Player, MatchLineup, MatchFixture

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception raised when dataset violates season or schema invariants."""
    pass


class SeasonValidator:
    def __init__(self):
        self.canonical_teams: Set[str] = set(SERIE_A_TEAMS_2026_2027.values())
        self.canonical_codes: Set[str] = set(SERIE_A_TEAMS_2026_2027.keys())
        self.promoted_teams: Set[str] = set(PROMOTED_TEAMS_2026_2027.values())
        self.relegated_teams: Set[str] = set(RELEGATED_TEAMS.values())
        self.relegated_codes: Set[str] = set(RELEGATED_TEAMS.keys())

    def validate_all(
        self,
        players: List[Player],
        lineups: List[MatchLineup],
        fixtures: List[MatchFixture]
    ) -> Dict[str, Any]:
        """
        Executes all validation checks and returns a summary report dictionary.
        Raises ValidationError if any critical invariant fails.
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "checks_passed": []
        }

        # 1. Validate Teams & Relegated Exclusion in Players
        player_teams = set(p.squadra for p in players)
        player_team_codes = set(p.squadra_code for p in players)

        # Check for relegated teams
        relegated_found = player_teams.intersection(self.relegated_teams)
        if relegated_found:
            msg = f"Relegated team(s) found in active players: {relegated_found}"
            results["errors"].append(msg)
            results["is_valid"] = False

        relegated_codes_found = player_team_codes.intersection(self.relegated_codes)
        if relegated_codes_found:
            msg = f"Relegated team code(s) found in active players: {relegated_codes_found}"
            results["errors"].append(msg)
            results["is_valid"] = False

        # Check promoted teams present
        missing_promoted = self.promoted_teams - player_teams
        if missing_promoted:
            msg = f"Missing promoted 2026/2027 team(s) in player database: {missing_promoted}"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append("All promoted 2026/2027 teams present in player database")

        # Check total teams count in players
        if len(player_teams) != 20:
            msg = f"Expected exactly 20 Serie A teams in player database, found {len(player_teams)}: {player_teams}"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append("Exactly 20 Serie A teams present in player database")

        # 2. Validate Player Counts & Invariants
        if len(players) < 500:
            msg = f"Player database count ({len(players)}) is below minimum threshold 500"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append(f"Total player count valid ({len(players)} >= 500)")

        role_counts = {"P": 0, "D": 0, "C": 0, "A": 0}
        for p in players:
            if p.ruolo not in role_counts:
                msg = f"Player {p.nome} has invalid role '{p.ruolo}'"
                results["errors"].append(msg)
                results["is_valid"] = False
            else:
                role_counts[p.ruolo] += 1

            if p.qa < 1 or p.fvm_1000 < 1 or p.prezzo_target < 1:
                msg = f"Player {p.nome} has invalid non-positive price metrics (qa={p.qa}, fvm={p.fvm_1000}, target={p.prezzo_target})"
                results["errors"].append(msg)
                results["is_valid"] = False

        if role_counts["P"] < 40 or role_counts["D"] < 120 or role_counts["C"] < 120 or role_counts["A"] < 80:
            msg = f"Role distribution insufficient: {role_counts}"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append(f"Role distribution valid: {role_counts}")

        # 3. Validate Lineups
        if len(lineups) != 10:
            msg = f"Expected 10 match lineups, found {len(lineups)}"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append("10 match lineups present")

        lineup_teams = set()
        for m in lineups:
            if not m.home_lineup or not m.away_lineup:
                msg = f"Match {m.match_id} missing home or away lineup"
                results["errors"].append(msg)
                results["is_valid"] = False
                continue

            lineup_teams.add(m.home_lineup.squadra)
            lineup_teams.add(m.away_lineup.squadra)

            # Check 11 starters per team
            if len(m.home_lineup.titolari) != 11:
                msg = f"Home team {m.home_lineup.squadra} has {len(m.home_lineup.titolari)} starters (expected 11)"
                results["errors"].append(msg)
                results["is_valid"] = False
            if len(m.away_lineup.titolari) != 11:
                msg = f"Away team {m.away_lineup.squadra} has {len(m.away_lineup.titolari)} starters (expected 11)"
                results["errors"].append(msg)
                results["is_valid"] = False

            # Check exactly 1 P in starters
            h_p = sum(1 for p in m.home_lineup.titolari if p.get("ruolo") == "P")
            a_p = sum(1 for p in m.away_lineup.titolari if p.get("ruolo") == "P")
            if h_p != 1:
                results["warnings"].append(f"Home team {m.home_lineup.squadra} has {h_p} GK starters")
            if a_p != 1:
                results["warnings"].append(f"Away team {m.away_lineup.squadra} has {a_p} GK starters")

        if len(lineup_teams) != 20:
            msg = f"Lineups cover {len(lineup_teams)} distinct teams (expected 20)"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append("All 20 Serie A clubs represented in matchday lineups")

        # 4. Validate Calendar Fixtures
        if len(fixtures) != 380:
            msg = f"Expected 380 fixtures in season calendar, found {len(fixtures)}"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append("Calendar contains all 380 Serie A fixtures")

        giornate = set(f.giornata for f in fixtures)
        if len(giornate) != 38 or set(range(1, 39)) != giornate:
            msg = f"Calendar missing matchdays: expected 1..38, found {len(giornate)} matchdays"
            results["errors"].append(msg)
            results["is_valid"] = False
        else:
            results["checks_passed"].append("All 38 matchdays present in calendar")

        # Check each team has 38 games (19 home, 19 away)
        team_home_counts = {t: 0 for t in self.canonical_teams}
        team_away_counts = {t: 0 for t in self.canonical_teams}
        for f in fixtures:
            if f.home_team in team_home_counts:
                team_home_counts[f.home_team] += 1
            if f.away_team in team_away_counts:
                team_away_counts[f.away_team] += 1

        for t in self.canonical_teams:
            if team_home_counts[t] != 19 or team_away_counts[t] != 19:
                results["warnings"].append(f"Team {t} has {team_home_counts[t]} home and {team_away_counts[t]} away matches (expected 19 each)")

        if not results["is_valid"]:
            logger.error(f"Validation failed with {len(results['errors'])} error(s): {results['errors']}")
            raise ValidationError(f"Data validation failed: {'; '.join(results['errors'])}")

        logger.info(f"All {len(results['checks_passed'])} validation checks passed successfully.")
        return results
