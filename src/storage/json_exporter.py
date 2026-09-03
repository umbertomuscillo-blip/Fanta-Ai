"""
JSON Exporter for Fantacalcio 2026/2027 Pipeline.
Saves structured JSON datasets and role-grouped players_db.json for dashboard compatibility.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import DATA_DIR, TEAMS_METADATA
from src.models import Player, MatchLineup, MatchFixture, SyncReport

logger = logging.getLogger(__name__)


class JsonExporter:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        players: Optional[List[Player]] = None,
        lineups: Optional[List[MatchLineup]] = None,
        fixtures: Optional[List[MatchFixture]] = None,
        sync_report: Optional[SyncReport] = None
    ) -> Dict[str, Path]:
        """
        Exports all available datasets to JSON in data/
        """
        exported = {}

        # 1. Teams
        teams_path = self.export_teams()
        exported["teams"] = teams_path

        # 2. Players
        if players is not None:
            p_path, db_path = self.export_players(players)
            exported["players"] = p_path
            exported["players_db"] = db_path

        # 3. Lineups
        if lineups is not None:
            l_paths = self.export_lineups(lineups)
            exported["lineups"] = l_paths[0]

        # 4. Fixtures
        if fixtures is not None:
            f_paths = self.export_fixtures(fixtures)
            exported["fixtures"] = f_paths[0]

        # 5. Sync Report
        if sync_report is not None:
            rep_path = self.export_sync_report(sync_report)
            exported["sync_report"] = rep_path

        return exported

    def export_teams(self) -> Path:
        target = self.output_dir / "teams.json"
        with open(target, "w", encoding="utf-8") as f:
            json.dump(TEAMS_METADATA, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(TEAMS_METADATA)} teams to {target}")
        return target

    def export_players(self, players: List[Player]) -> tuple[Path, Path]:
        # Flat JSON
        flat_players = [p.to_dict() for p in players]
        flat_path = self.output_dir / "players.json"
        with open(flat_path, "w", encoding="utf-8") as f:
            json.dump(flat_players, f, ensure_ascii=False, indent=2)

        # Role-grouped JSON for dashboard/index.html compatibility
        by_role: Dict[str, List[Dict[str, Any]]] = {"P": [], "D": [], "C": [], "A": []}
        for p in players:
            r = p.ruolo if p.ruolo in by_role else "D"
            # Format expected by dashboard
            by_role[r].append({
                "id": p.id,
                "nome": p.nome,
                "squadra": p.squadra,
                "squadra_code": p.squadra_code,
                "ruolo": p.ruolo,
                "ruolo_mantra": p.ruolo_mantra,
                "qa": p.qa,
                "qi": p.qi,
                "fvm_1000": p.fvm_1000,
                "prezzo_target": p.prezzo_target,
                "prezzo_max": p.prezzo_max,
                "tier": p.tier,
                "piazzati": p.piazzati,
                "mod_rating": p.mod_rating,
                "note": p.note,
                "mv": p.mv,
                "fm": p.fm,
                "xg": p.xg,
                "xa": p.xa,
                "xg_90": p.xg_90,
                "xa_90": p.xa_90,
                "moneyball_index": p.moneyball_index,
                "stats": p.stats.to_dict() if hasattr(p.stats, "to_dict") else p.stats
            })

        db_path = self.output_dir / "players_db.json"
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(by_role, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(players)} players to {flat_path} and {db_path}")
        return flat_path, db_path

    def export_lineups(self, lineups: List[MatchLineup]) -> tuple[Path, Path]:
        data = {
            "giornata": lineups[0].giornata if lineups else 1,
            "season": "2026/2027",
            "matches": [m.to_dict() for m in lineups]
        }

        # Write primary filename probabili_formazioni.json and alias lineups.json
        p1 = self.output_dir / "probabili_formazioni.json"
        p2 = self.output_dir / "lineups.json"

        with open(p1, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(lineups)} match lineups to {p1} and {p2}")
        return p1, p2

    def export_fixtures(self, fixtures: List[MatchFixture]) -> tuple[Path, Path]:
        data = [f.to_dict() for f in fixtures]

        p1 = self.output_dir / "calendario_serie_a.json"
        p2 = self.output_dir / "calendar.json"

        with open(p1, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(fixtures)} fixtures to {p1} and {p2}")
        return p1, p2

    def export_sync_report(self, report: SyncReport) -> Path:
        target = self.output_dir / "sync_report.json"
        with open(target, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Saved sync report to {target}")
        return target
