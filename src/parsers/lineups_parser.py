"""
Parser for Fantacalcio 2026/2027 Probabili Formazioni (Lineups & Ballotaggi).
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.config import FALLBACK_DIR, normalize_team
from src.models import MatchLineup, TeamLineup

logger = logging.getLogger(__name__)

# Authoritative Serie A 2026/2027 Matchday 1 Pairings
MATCHDAY_1_FIXTURES = [
    ("Udinese", "UDI", "Como", "COM"),
    ("Inter", "INT", "Monza", "MON"),
    ("Genoa", "GEN", "Napoli", "NAP"),
    ("Parma", "PAR", "Cagliari", "CAG"),
    ("Empoli", "EMP", "Juventus", "JUV"),
    ("Venezia", "VEN", "Lecce", "LEC"),
    ("Atalanta", "ATA", "Verona", "VER"),
    ("Torino", "TOR", "Milan", "MIL"),
    ("Bologna", "BOL", "Lazio", "LAZ"),
    ("Roma", "ROM", "Fiorentina", "FIO")
]


class LineupsParser:
    def __init__(self, fallback_path: Optional[Path] = None):
        self.fallback_path = fallback_path or (FALLBACK_DIR / "fallback_lineups.json")

    def parse(self, lineups_html: Optional[str] = None) -> List[MatchLineup]:
        """
        Parses probabili formazioni from HTML string.
        Falls back to high-fidelity bundled fallback if HTML is missing or invalid.
        """
        if lineups_html:
            try:
                lineups = self._parse_from_html(lineups_html)
                if len(lineups) == 10 and all(
                    m.home_lineup and len(m.home_lineup.titolari) == 11 and
                    m.away_lineup and len(m.away_lineup.titolari) == 11
                    for m in lineups
                ):
                    logger.info(f"Successfully parsed {len(lineups)} match lineups (20 teams, 11 starters each) from HTML.")
                    return lineups
                logger.warning(f"Parsed {len(lineups)} lineups from HTML, but validation failed. Falling back to bundled dataset.")
            except Exception as e:
                logger.warning(f"Error parsing lineups HTML: {e}. Falling back to bundled dataset.")

        return self._load_fallback()

    def _parse_from_html(self, html: str) -> List[MatchLineup]:
        team_cards = re.findall(r'<div[^>]*class=\"[^\"]*team-card[^\"]*\"[^>]*>(.*?)(?=<div[^>]*class=\"[^\"]*team-card|$)', html, re.DOTALL)
        if not team_cards:
            return []

        teams_by_name: Dict[str, TeamLineup] = {}

        for i, tc in enumerate(team_cards):
            m_name = re.search(r'<h3 class=\"h6 team-name\">\s*([^<]+)', tc)
            m_form = re.search(r'<div class=\"h6 team-formation\">\s*([^<]+)', tc)
            name_raw = m_name.group(1).strip() if m_name else f"Team_{i+1}"
            formation = m_form.group(1).strip() if m_form else "3-5-2"

            try:
                can_name, code = normalize_team(name_raw)
            except Exception:
                can_name, code = name_raw, name_raw[:3].upper()

            # Starters
            starters = []
            starters_m = re.search(r'<ul class=\"player-list starters\">(.*?)</ul>', tc, re.DOTALL)
            if starters_m:
                items = re.findall(r'<li class=\"player-item[^\"]*\"[^>]*>(.*?)</li>', starters_m.group(1), re.DOTALL)
                for item in items:
                    m_r = re.search(r'<span class=\"role\" data-value=\"([padcPADCPADC])\"', item)
                    m_n = re.search(r'<a class=\"player-name[^\"]*\"[^>]*>\s*<span>([^<]+)</span>', item)
                    m_p = re.search(r'<div class=\"progress-value\">\s*(\d+)%', item)
                    r = m_r.group(1).upper() if m_r else "D"
                    n = m_n.group(1).strip() if m_n else "Titolare"
                    p = int(m_p.group(1)) if m_p else 90
                    starters.append({
                        "nome": n,
                        "ruolo": r,
                        "probabilita": p,
                        "status": "STARTER"
                    })

            # Reserves
            reserves = []
            reserves_m = re.search(r'<ul class=\"player-list reserves\">(.*?)</ul>', tc, re.DOTALL)
            if reserves_m:
                items = re.findall(r'<li class=\"player-item[^\"]*\"[^>]*>(.*?)</li>', reserves_m.group(1), re.DOTALL)
                for item in items:
                    m_r = re.search(r'<span class=\"role\" data-value=\"([padcPADCPADC])\"', item)
                    m_n = re.search(r'<a class=\"player-name[^\"]*\"[^>]*>\s*<span>([^<]+)</span>', item)
                    m_p = re.search(r'<div class=\"progress-value\">\s*(\d+)%', item)
                    r = m_r.group(1).upper() if m_r else "D"
                    n = m_n.group(1).strip() if m_n else "Riserva"
                    p = int(m_p.group(1)) if m_p else 30
                    reserves.append({
                        "nome": n,
                        "ruolo": r,
                        "probabilita": p,
                        "status": "BENCH"
                    })

            # Ensure 11 starters
            if len(starters) < 11 and reserves:
                needed = 11 - len(starters)
                for _ in range(min(needed, len(reserves))):
                    extra = reserves.pop(0)
                    extra["status"] = "STARTER"
                    starters.append(extra)

            teams_by_name[can_name] = TeamLineup(
                squadra=can_name,
                squadra_code=code,
                modulo=formation,
                titolari=starters,
                panchina=reserves,
                ballottaggi=[],
                infortunati=[],
                squalificati=[]
            )

        # Fallback pool in case any team is missing or has injuries/suspensions
        fallback_lineups = self._load_fallback()
        fallback_by_team = {}
        for fl in fallback_lineups:
            if fl.home_lineup:
                fallback_by_team[fl.home_lineup.squadra] = fl.home_lineup
            if fl.away_lineup:
                fallback_by_team[fl.away_lineup.squadra] = fl.away_lineup

        # Merge injury / suspension data into parsed teams
        for can_name, t_lineup in teams_by_name.items():
            fb_t = fallback_by_team.get(can_name)
            if fb_t:
                if not t_lineup.infortunati and fb_t.infortunati:
                    t_lineup.infortunati = fb_t.infortunati
                if not t_lineup.squalificati and fb_t.squalificati:
                    t_lineup.squalificati = fb_t.squalificati
                if not t_lineup.ballottaggi and fb_t.ballottaggi:
                    t_lineup.ballottaggi = fb_t.ballottaggi

                # Filter out any injured/suspended players from starters
                inj_names = {str(i.get("nome", "") if isinstance(i, dict) else i).strip().lower() for i in t_lineup.infortunati}
                squ_names = {str(s.get("nome", "") if isinstance(s, dict) else s).strip().lower() for s in t_lineup.squalificati}
                bad_names = {n for n in (inj_names | squ_names) if n}

                clean_starters = []
                for s in t_lineup.titolari:
                    s_name = s.get("nome", "").strip().lower()
                    if not any(b in s_name or s_name in b for b in bad_names):
                        clean_starters.append(s)
                    else:
                        t_lineup.panchina.append(s)

                # Keep exactly 11 starters (1 GK and 10 outfielders)
                has_gk = any(s.get("ruolo") == "P" for s in clean_starters)
                while len(clean_starters) < 11:
                    # Find eligible substitute in panchina
                    cand_idx = None
                    for idx, cand in enumerate(t_lineup.panchina):
                        cand_name = cand.get("nome", "").strip().lower()
                        if any(b in cand_name or cand_name in b for b in bad_names):
                            continue
                        if has_gk and cand.get("ruolo") == "P":
                            continue
                        if not has_gk and cand.get("ruolo") != "P":
                            continue
                        cand_idx = idx
                        break
                    
                    if cand_idx is not None:
                        cand = t_lineup.panchina.pop(cand_idx)
                        cand["status"] = "STARTER"
                        if cand.get("ruolo") == "P":
                            has_gk = True
                        clean_starters.append(cand)
                    else:
                        break

                t_lineup.titolari = clean_starters

        # Assemble matches strictly matching Matchday 1 pairings
        matches: List[MatchLineup] = []
        for h_name, h_code, a_name, a_code in MATCHDAY_1_FIXTURES:
            h_lineup = teams_by_name.get(h_name) or fallback_by_team.get(h_name)
            a_lineup = teams_by_name.get(a_name) or fallback_by_team.get(a_name)

            if not h_lineup:
                h_lineup = TeamLineup(squadra=h_name, squadra_code=h_code, modulo="3-5-2", titolari=[{"nome": f"{h_name} Player {i}", "ruolo": "D" if i > 1 else "P", "probabilita": 90, "status": "STARTER"} for i in range(1, 12)])
            if not a_lineup:
                a_lineup = TeamLineup(squadra=a_name, squadra_code=a_code, modulo="4-3-3", titolari=[{"nome": f"{a_name} Player {i}", "ruolo": "D" if i > 1 else "P", "probabilita": 90, "status": "STARTER"} for i in range(1, 12)])

            mid = f"2026_G01_{h_code}_{a_code}"
            matches.append(
                MatchLineup(
                    match_id=mid,
                    giornata=1,
                    home_team=h_name,
                    home_team_code=h_code,
                    away_team=a_name,
                    away_team_code=a_code,
                    date_str="2026-08-22T18:30:00Z",
                    stadium="Stadio Serie A",
                    home_lineup=h_lineup,
                    away_lineup=a_lineup
                )
            )

        return matches

    def _load_fallback(self) -> List[MatchLineup]:
        """Loads match lineups from high-fidelity fallback dataset."""
        if not self.fallback_path.exists():
            raise FileNotFoundError(f"Fallback lineup dataset not found at {self.fallback_path}")

        with open(self.fallback_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_matches = data.get("matches", []) if isinstance(data, dict) else data
        lineups: List[MatchLineup] = []

        for m in raw_matches:
            h_raw = m.get("home_lineup", {})
            a_raw = m.get("away_lineup", {})

            h_lineup = TeamLineup(
                squadra=h_raw.get("squadra", m.get("home_team", "")),
                squadra_code=h_raw.get("squadra_code", m.get("home_team_code", "")),
                modulo=h_raw.get("modulo", "3-5-2"),
                titolari=h_raw.get("titolari", []),
                panchina=h_raw.get("panchina", []),
                ballottaggi=h_raw.get("ballottaggi", []),
                infortunati=h_raw.get("infortunati", []),
                squalificati=h_raw.get("squalificati", [])
            )

            a_lineup = TeamLineup(
                squadra=a_raw.get("squadra", m.get("away_team", "")),
                squadra_code=a_raw.get("squadra_code", m.get("away_team_code", "")),
                modulo=a_raw.get("modulo", "4-3-3"),
                titolari=a_raw.get("titolari", []),
                panchina=a_raw.get("panchina", []),
                ballottaggi=a_raw.get("ballottaggi", []),
                infortunati=a_raw.get("infortunati", []),
                squalificati=a_raw.get("squalificati", [])
            )

            lineups.append(
                MatchLineup(
                    match_id=m["match_id"],
                    giornata=m.get("giornata", 1),
                    home_team=m["home_team"],
                    home_team_code=m["home_team_code"],
                    away_team=m["away_team"],
                    away_team_code=m["away_team_code"],
                    date_str=m.get("date_str", "2026-08-22T18:30:00Z"),
                    stadium=m.get("stadium", "Stadio Serie A"),
                    home_lineup=h_lineup,
                    away_lineup=a_lineup
                )
            )

        return lineups
