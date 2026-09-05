"""
Injury, News & Lineup Intelligence Engine - Fantacalcio 2026/2027.
Monitors injuries, suspensions, recovery times, ballottaggi, and training news.
Generates structured intelligence for the Lineup Optimizer.
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"


@dataclass
class PlayerInjuryStatus:
    nome: str
    squadra: str
    ruolo: str
    status: str  # "AVAILABLE", "BALLOTTAGGIO", "INJURED", "SUSPENDED", "BENCH"
    titolare_pct: int  # 0 to 100
    ballottaggio_con: Optional[str] = None
    ballottaggio_pct: Optional[int] = None
    motivo_indisponibilita: Optional[str] = None
    rientro_previsto: Optional[str] = None
    note_allenamento: Optional[str] = None
    affidabilita_voto: float = 1.0  # 0.0 to 1.0 multiplier


class InjuryNewsEngine:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DATA_DIR
        self.players_db_file = self.data_dir / "players.json"
        self.probabili_file = self.data_dir / "probabili_formazioni.json"
        self.output_report_file = self.data_dir / "injury_news_report.json"

    def analyze_status(self) -> Dict[str, Any]:
        report: Dict[str, PlayerInjuryStatus] = {}
        
        players = []
        if self.players_db_file.exists():
            with open(self.players_db_file, "r", encoding="utf-8") as f:
                players = json.load(f)

        for p in players:
            name = p.get("nome", "")
            team = p.get("squadra", "")
            role = p.get("ruolo", "C")
            report[name] = PlayerInjuryStatus(
                nome=name,
                squadra=team,
                ruolo=role,
                status="AVAILABLE",
                titolare_pct=80,
                affidabilita_voto=0.9
            )

        if self.probabili_file.exists():
            try:
                with open(self.probabili_file, "r", encoding="utf-8") as f:
                    pf_data = json.load(f)
                    matches = pf_data.get("matches", [])
                    for match in matches:
                        for side in ["home_lineup", "away_lineup"]:
                            lineup = match.get(side, {})
                            t_name = lineup.get("squadra", "")
                            
                            for starter in lineup.get("titolari", []):
                                s_name = starter.get("nome", "")
                                pct = starter.get("probabilita", 90)
                                if s_name in report:
                                    report[s_name].status = "AVAILABLE"
                                    report[s_name].titolare_pct = pct
                                    report[s_name].affidabilita_voto = min(1.0, pct / 100.0)

                            for bencher in lineup.get("panchina", []):
                                b_name = bencher.get("nome", "")
                                pct = bencher.get("probabilita", 35)
                                if b_name in report:
                                    report[b_name].status = "BENCH"
                                    report[b_name].titolare_pct = pct
                                    report[b_name].affidabilita_voto = 0.45

                            for b in lineup.get("ballottaggi", []):
                                p_in = b.get("in", "")
                                p_out = b.get("out", "")
                                pct_in = b.get("pct_in", 55)
                                pct_out = 100 - pct_in
                                
                                if p_in in report:
                                    report[p_in].status = "BALLOTTAGGIO"
                                    report[p_in].titolare_pct = pct_in
                                    report[p_in].ballottaggio_con = p_out
                                    report[p_in].ballottaggio_pct = pct_out
                                    report[p_in].affidabilita_voto = pct_in / 100.0
                                
                                if p_out in report:
                                    report[p_out].status = "BALLOTTAGGIO"
                                    report[p_out].titolare_pct = pct_out
                                    report[p_out].ballottaggio_con = p_in
                                    report[p_out].ballottaggio_pct = pct_in
                                    report[p_out].affidabilita_voto = pct_out / 100.0

                            for inj in lineup.get("indisponibili", []):
                                i_name = inj.get("nome", "")
                                reason = inj.get("motivo", "Infortunio muscolare")
                                rientro = inj.get("rientro", "Da valutare")
                                is_susp = "squalifica" in reason.lower()
                                
                                if i_name in report:
                                    report[i_name].status = "SUSPENDED" if is_susp else "INJURED"
                                    report[i_name].titolare_pct = 0
                                    report[i_name].affidabilita_voto = 0.0
                                    report[i_name].motivo_indisponibilita = reason
                                    report[i_name].rientro_previsto = rientro
            except Exception as e:
                logger.error(f"Error parsing probabili formazioni in InjuryNewsEngine: {e}")

        serialized = {k: asdict(v) for k, v in report.items()}
        with open(self.output_report_file, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)

        return serialized

    def get_player_status(self, player_name: str) -> Optional[PlayerInjuryStatus]:
        if not self.output_report_file.exists():
            self.analyze_status()

        with open(self.output_report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        p_data = data.get(player_name)
        if p_data:
            return PlayerInjuryStatus(**p_data)
        
        for k, v in data.items():
            if player_name.lower() in k.lower() or k.lower() in player_name.lower():
                return PlayerInjuryStatus(**v)
                
        return None

if __name__ == "__main__":
    engine = InjuryNewsEngine()
    rep = engine.analyze_status()
    print("SUCCESS: Injury report generated for", len(rep), "players.")
