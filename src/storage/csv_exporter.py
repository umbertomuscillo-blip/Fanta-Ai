"""
CSV Exporter for Fantacalcio 2026/2027 Pipeline.
Saves tabular CSV datasets for AI models and spreadsheet analyses.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import DATA_DIR, TEAMS_METADATA
from src.models import Player, MatchLineup, MatchFixture

logger = logging.getLogger(__name__)


class CsvExporter:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        players: Optional[List[Player]] = None,
        lineups: Optional[List[MatchLineup]] = None,
        fixtures: Optional[List[MatchFixture]] = None
    ) -> Dict[str, Path]:
        exported = {}

        teams_path = self.export_teams()
        exported["teams"] = teams_path

        if players is not None:
            p_path = self.export_players(players)
            exported["players"] = p_path

        if lineups is not None:
            l_paths = self.export_lineups(lineups)
            exported["lineups"] = l_paths[0]

        if fixtures is not None:
            f_paths = self.export_fixtures(fixtures)
            exported["fixtures"] = f_paths[0]

        return exported

    def export_teams(self) -> Path:
        target = self.output_dir / "teams.csv"
        fieldnames = ["id", "code", "name", "full_name", "city", "stadium", "coach", "promoted", "primary_color", "secondary_color"]

        with open(target, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in TEAMS_METADATA:
                writer.writerow(t)

        logger.info(f"Saved {len(TEAMS_METADATA)} teams to {target}")
        return target

    def export_players(self, players: List[Player]) -> Path:
        target = self.output_dir / "players.csv"
        fieldnames = [
            "id", "nome", "squadra", "squadra_code", "ruolo", "ruolo_mantra",
            "qa", "qi", "fvm_1000", "prezzo_target", "prezzo_max", "tier",
            "piazzati", "mod_rating", "presenze", "media_voto", "fantamedia",
            "gol", "gol_subiti", "rigori_segnati", "rigori_sbagliati",
            "rigori_parati", "assist", "ammonizioni", "espulsioni", "clean_sheets",
            "xg", "xa", "xg_90", "xa_90", "moneyball_index",
            "titolare_probabile", "note", "updated_at"
        ]

        with open(target, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in players:
                writer.writerow(p.to_csv_dict())

        logger.info(f"Saved {len(players)} players to {target}")
        return target

    def export_lineups(self, lineups: List[MatchLineup]) -> tuple[Path, Path]:
        p1 = self.output_dir / "probabili_formazioni.csv"
        p2 = self.output_dir / "lineups.csv"

        fieldnames = [
            "giornata", "match_id", "team", "team_code", "is_home", "opponent", "opponent_code",
            "formation", "player_name", "ruolo", "status", "probability"
        ]

        rows = []
        for m in lineups:
            for is_home, t, opp in [(True, m.home_lineup, m.away_lineup), (False, m.away_lineup, m.home_lineup)]:
                if not t:
                    continue
                opp_name = opp.squadra if opp else ""
                opp_code = opp.squadra_code if opp else ""

                for p in t.titolari:
                    rows.append({
                        "giornata": m.giornata,
                        "match_id": m.match_id,
                        "team": t.squadra,
                        "team_code": t.squadra_code,
                        "is_home": is_home,
                        "opponent": opp_name,
                        "opponent_code": opp_code,
                        "formation": t.modulo,
                        "player_name": p.get("nome", ""),
                        "ruolo": p.get("ruolo", ""),
                        "status": "STARTER",
                        "probability": p.get("probabilita", 90)
                    })

                for p in t.panchina:
                    rows.append({
                        "giornata": m.giornata,
                        "match_id": m.match_id,
                        "team": t.squadra,
                        "team_code": t.squadra_code,
                        "is_home": is_home,
                        "opponent": opp_name,
                        "opponent_code": opp_code,
                        "formation": t.modulo,
                        "player_name": p.get("nome", ""),
                        "ruolo": p.get("ruolo", ""),
                        "status": "BENCH",
                        "probability": p.get("probabilita", 30)
                    })

        for p in [p1, p2]:
            with open(p, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)

        logger.info(f"Saved {len(rows)} lineup player rows to {p1} and {p2}")
        return p1, p2

    def export_fixtures(self, fixtures: List[MatchFixture]) -> tuple[Path, Path]:
        p1 = self.output_dir / "calendario_serie_a.csv"
        p2 = self.output_dir / "calendar.csv"

        fieldnames = [
            "match_id", "giornata", "season", "date_str", "home_team", "home_team_code",
            "away_team", "away_team_code", "home_score", "away_score", "status",
            "difficolta_home", "difficolta_away"
        ]

        for p in [p1, p2]:
            with open(p, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for fix in fixtures:
                    writer.writerow(fix.to_csv_dict())

        logger.info(f"Saved {len(fixtures)} fixtures to {p1} and {p2}")
        return p1, p2
