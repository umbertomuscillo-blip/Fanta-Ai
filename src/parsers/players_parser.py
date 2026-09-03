"""
Parser for Fantacalcio 2026/2027 Players, Quotazioni, and Statistics.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.config import (
    FALLBACK_DIR,
    normalize_team,
    PENALTY_TAKERS,
    MOD_DEFENDERS,
    AUCTION_CONFIG,
    SERIE_A_TEAMS_2026_2027
)
from src.models import Player, PlayerStats

logger = logging.getLogger(__name__)


def compute_moneyball_metrics(
    ruolo: str,
    fvm_1000: int,
    prezzo_target: int,
    gol: int = 0,
    assist: int = 0,
    mv: float = 0.0,
    fm: float = 0.0,
    piazzati: str = "",
    mod_rating: str = "",
    clean_sheets: int = 0,
    gol_subiti: int = 0,
    existing_xg: float = 0.0,
    existing_xa: float = 0.0,
    existing_xg_90: float = 0.0,
    existing_xa_90: float = 0.0,
    existing_moneyball: float = 0.0
) -> Dict[str, float]:
    """
    Computes expected goals (xG), expected assists (xA), per-90 rates,
    and a normalized Moneyball Index (0-100) assessing performance-to-cost value.
    """
    if existing_xg > 0.0 or existing_xa > 0.0 or existing_moneyball > 0.0:
        xg = existing_xg
        xa = existing_xa
        xg_90 = existing_xg_90 if existing_xg_90 > 0.0 else round(xg / 34.0, 2)
        xa_90 = existing_xa_90 if existing_xa_90 > 0.0 else round(xa / 34.0, 2)
        mb = existing_moneyball
        return {"xg": xg, "xa": xa, "xg_90": xg_90, "xa_90": xa_90, "moneyball_index": mb}

    role = ruolo.upper()
    is_penalty = "Rigorista" in piazzati or "1° Rigorista" in piazzati
    is_set_piece = "Punizioni" in piazzati or "Corner" in piazzati

    if role == "P":
        xg = 0.0
        xa = 0.0
        xg_90 = 0.0
        xa_90 = 0.0
        cost = max(1, prezzo_target)
        if fvm_1000 >= 30:
            mb = round(min(96.0, max(50.0, 88.0 - (cost * 0.25) + (clean_sheets * 2.0) + (max(5.8, mv) - 6.0) * 10.0)), 2)
        else:
            mb = round(min(98.0, max(45.0, 72.0 + (35.0 / max(2, cost)) + (max(5.8, mv) - 6.0) * 15.0)), 2)
    elif role == "D":
        has_mod = bool(mod_rating) or (mv >= 6.2)
        base_xg = round(max(0.05, (fvm_1000 / 85.0) + (gol * 0.6) + (0.5 if has_mod else 0.0)), 2)
        base_xa = round(max(0.05, (fvm_1000 / 55.0) + (assist * 0.7) + (0.8 if is_set_piece else 0.0)), 2)
        xg = base_xg
        xa = base_xa
        xg_90 = round(xg / 34.0, 2)
        xa_90 = round(xa / 34.0, 2)
        cost = max(1, prezzo_target)
        exp_pts = (xg * 3.0) + (xa * 1.0) + ((max(5.8, mv) - 5.8) * 12.0) + (4.0 if has_mod else 0.0)
        mb = round(min(99.0, max(20.0, 45.0 + (exp_pts * 3.8) / (cost ** 0.55))), 2)
    elif role == "C":
        base_xg = round(max(0.1, (fvm_1000 / 40.0) + (gol * 0.75) + (1.5 if is_penalty else 0.0)), 2)
        base_xa = round(max(0.15, (fvm_1000 / 35.0) + (assist * 0.8) + (1.2 if is_set_piece else 0.0)), 2)
        xg = base_xg
        xa = base_xa
        xg_90 = round(xg / 34.0, 2)
        xa_90 = round(xa / 34.0, 2)
        cost = max(1, prezzo_target)
        exp_pts = (xg * 3.0) + (xa * 1.0) + ((max(5.8, mv) - 5.8) * 10.0)
        mb = round(min(99.0, max(20.0, 40.0 + (exp_pts * 3.2) / (cost ** 0.58))), 2)
    else:
        base_xg = round(max(0.4, (fvm_1000 / 22.0) + (gol * 0.85) + (2.5 if is_penalty else 0.0)), 2)
        base_xa = round(max(0.2, (fvm_1000 / 60.0) + (assist * 0.7)), 2)
        xg = base_xg
        xa = base_xa
        xg_90 = round(xg / 34.0, 2)
        xa_90 = round(xa / 34.0, 2)
        cost = max(1, prezzo_target)
        exp_pts = (xg * 3.0) + (xa * 1.0) + ((max(5.8, mv) - 5.8) * 8.0)
        mb = round(min(99.0, max(20.0, 38.0 + (exp_pts * 2.8) / (cost ** 0.60))), 2)

    return {"xg": xg, "xa": xa, "xg_90": xg_90, "xa_90": xa_90, "moneyball_index": mb}


class PlayersParser:
    def __init__(self, fallback_path: Optional[Path] = None):
        self.fallback_path = fallback_path or (FALLBACK_DIR / "fallback_players.json")

    def parse(
        self,
        quotazioni_html: Optional[str] = None,
        stats_html: Optional[str] = None
    ) -> List[Player]:
        """
        Parses players from HTML strings. If parsing fails or data is insufficient,
        falls back to bundled high-fidelity dataset.
        """
        if quotazioni_html:
            try:
                players = self._parse_from_html(quotazioni_html, stats_html)
                if len(players) >= 500:
                    logger.info(f"Successfully parsed {len(players)} players from live/cached HTML.")
                    return players
                logger.warning(f"Parsed only {len(players)} players (<500 threshold). Falling back to bundled dataset.")
            except Exception as e:
                logger.warning(f"Error parsing HTML: {e}. Falling back to bundled dataset.")

        return self._load_fallback()

    def _parse_from_html(
        self,
        quotazioni_html: str,
        stats_html: Optional[str] = None
    ) -> List[Player]:
        # 1. Parse statistics map
        stats_map: Dict[str, PlayerStats] = {}
        if stats_html:
            s_rows = re.findall(r'<tr[^>]*class=\"[^\"]*player-row[^\"]*\"[^>]*>(.*?)</tr>', stats_html, re.DOTALL)
            for r in s_rows:
                m_name = re.search(r'<span>([^<]+)</span>\s*</a>', r)
                if not m_name:
                    continue
                name = m_name.group(1).strip()

                m_pg = re.search(r'data-col-key=\"pg\"[^>]*>\s*(\d+)', r)
                m_mv = re.search(r'data-col-key=\"mv\"[^>]*>\s*([0-9,]+)', r)
                m_mfv = re.search(r'data-col-key=\"mfv\"[^>]*>\s*([0-9,]+)', r)
                m_gol = re.search(r'data-col-key=\"gol\"[^>]*>\s*(\d+)', r)
                m_gs = re.search(r'data-col-key=\"gs\"[^>]*>\s*(\d+)', r)
                m_rig = re.search(r'data-col-key=\"rig\"[^>]*>\s*(\d+)\s*/\s*(\d+)', r)
                m_rp = re.search(r'data-col-key=\"rp\"[^>]*>\s*(\d+)', r)
                m_ass = re.search(r'data-col-key=\"ass\"[^>]*>\s*(\d+)', r)
                m_amm = re.search(r'data-col-key=\"amm\"[^>]*>\s*(\d+)', r)
                m_esp = re.search(r'data-col-key=\"esp\"[^>]*>\s*(\d+)', r)

                def parse_float(m_val):
                    if not m_val:
                        return 0.0
                    clean = m_val.group(1).replace(",", ".").strip()
                    try:
                        return float(clean)
                    except ValueError:
                        return 0.0

                def parse_int(m_val):
                    if not m_val:
                        return 0
                    try:
                        return int(m_val.group(1).strip())
                    except ValueError:
                        return 0

                mv = parse_float(m_mv)
                fm = parse_float(m_mfv)
                pg = parse_int(m_pg)
                gol = parse_int(m_gol)
                gs = parse_int(m_gs)
                rig_s = int(m_rig.group(1)) if m_rig else 0
                rig_tot = int(m_rig.group(2)) if m_rig else 0
                rig_miss = max(0, rig_tot - rig_s)
                rp = parse_int(m_rp)
                ass = parse_int(m_ass)
                amm = parse_int(m_amm)
                esp = parse_int(m_esp)

                stats_map[name.lower()] = PlayerStats(
                    partite_a_voto=pg,
                    media_voto=mv,
                    fantamedia=fm,
                    gol=gol,
                    gol_subiti=gs,
                    rigori_segnati=rig_s,
                    rigori_sbagliati=rig_miss,
                    rigori_parati=rp,
                    assist=ass,
                    ammonizioni=amm,
                    espulsioni=esp,
                    clean_sheets=0
                )

        # 2. Parse quotazioni table
        q_rows = re.findall(r'<tr[^>]*class=\"[^\"]*player-row[^\"]*\"[^>]*>(.*?)</tr>', quotazioni_html, re.DOTALL)
        players: List[Player] = []

        for idx, r in enumerate(q_rows, 1):
            m_name = re.search(r'<span>([^<]+)</span>\s*</a>', r)
            if not m_name:
                continue
            name = m_name.group(1).strip()

            m_role = re.search(r'<th class=\"player-role player-role-classic\">\s*<span class=\"role\" data-value=\"([padcPADCPADC])\"', r)
            role = m_role.group(1).upper() if m_role else "D"
            if role not in {"P", "D", "C", "A"}:
                role = "D"

            m_mantra = re.findall(r'<span class=\"role role-mantra\" data-value=\"([^\"]+)\"', r)
            mantra_roles = ";".join(m_mantra) if m_mantra else ("por" if role == "P" else role.lower())

            m_team = re.search(r'<td class=\"player-team\" data-col-key=\"sq\">\s*([^<\s]+)', r)
            team_raw = m_team.group(1).strip() if m_team else "INT"

            try:
                can_team, team_code = normalize_team(team_raw)
            except Exception:
                can_team, team_code = "Inter", "INT"

            m_qa = re.search(r'<td class=\"player-classic-current-price\" data-col-key=\"c_qa\">\s*(\d+)', r)
            qa = int(m_qa.group(1)) if m_qa else 1

            m_qi = re.search(r'<td class=\"player-classic-initial-price\" data-col-key=\"c_qi\">\s*(\d+)', r)
            qi = int(m_qi.group(1)) if m_qi else 1

            m_fvm = re.search(r'<td class=\"player-classic-fvm\" data-col-key=\"c_fvm\">\s*(\d+)', r)
            fvm = int(m_fvm.group(1)) if m_fvm else 1

            m_id = re.search(r'href=\"[^\"]*/(\d+)\"', r)
            pid = int(m_id.group(1)) if m_id else idx

            # Scaled 500 budget
            target_500 = max(AUCTION_CONFIG["min_price"], round(fvm / 2))
            max_500 = max(AUCTION_CONFIG["min_price"], round(target_500 * AUCTION_CONFIG["max_bid_multiplier"]))

            # Tier classification
            tier = "Regolare"
            if role == "P":
                tier = "1 Top Portiere" if target_500 >= 30 else "2 Semi-Top" if target_500 >= 20 else "3 Titolare Medio" if target_500 >= 10 else "4 Low-Cost / Riserva"
            elif role == "D":
                tier = "1 Top Difesa" if target_500 >= 20 else "2 Semi-Top / Mod" if target_500 >= 10 else "3 Titolare Low-Cost" if target_500 >= 5 else "4 Riserva a 1 cr"
            elif role == "C":
                tier = "1 Top Centrocampo" if target_500 >= 30 else "2 Semi-Top Bonus" if target_500 >= 18 else "3 Titolare / Scommessa" if target_500 >= 8 else "4 Low-Cost a 1 cr"
            elif role == "A":
                tier = "1 Top Assoluto (1° Slot)" if target_500 >= 100 else "2 Secondo Slot di Lusso" if target_500 >= 50 else "3 Terzo Slot Titolare" if target_500 >= 20 else "4 Quarto/Quinto Slot" if target_500 >= 8 else "5 Scommessa / Riserva"

            piazzati = ""
            for pk, pv in PENALTY_TAKERS.items():
                if pk.lower() in name.lower():
                    piazzati = pv
                    break

            mod_rating = ""
            note = ""
            for mk, mv in MOD_DEFENDERS.items():
                if mk.lower() in name.lower():
                    mod_rating = mv["mod"]
                    note = mv["note"]
                    break

            st = stats_map.get(name.lower(), PlayerStats())
            mb_data = compute_moneyball_metrics(
                ruolo=role,
                fvm_1000=fvm,
                prezzo_target=target_500,
                gol=st.gol,
                assist=st.assist,
                mv=st.media_voto,
                fm=st.fantamedia,
                piazzati=piazzati,
                mod_rating=mod_rating,
                clean_sheets=st.clean_sheets,
                gol_subiti=st.gol_subiti
            )

            st.xg = mb_data["xg"]
            st.xa = mb_data["xa"]
            st.xg_90 = mb_data["xg_90"]
            st.xa_90 = mb_data["xa_90"]
            st.moneyball_index = mb_data["moneyball_index"]

            player = Player(
                id=pid,
                nome=name,
                squadra=can_team,
                squadra_code=team_code,
                ruolo=role,
                ruolo_mantra=mantra_roles,
                qa=qa,
                qi=qi,
                fvm_1000=fvm,
                prezzo_target=target_500,
                prezzo_max=max_500,
                tier=tier,
                piazzati=piazzati,
                mod_rating=mod_rating,
                mv=st.media_voto,
                fm=st.fantamedia,
                xg=mb_data["xg"],
                xa=mb_data["xa"],
                xg_90=mb_data["xg_90"],
                xa_90=mb_data["xa_90"],
                moneyball_index=mb_data["moneyball_index"],
                note=note,
                is_starter=True,
                stats=st
            )
            players.append(player)

        players.sort(key=lambda x: x.fvm_1000, reverse=True)
        return players

    def _load_fallback(self) -> List[Player]:
        """Loads players from high-fidelity fallback dataset."""
        logger.info(f"Loading fallback players from {self.fallback_path}")
        if not self.fallback_path.exists():
            raise FileNotFoundError(f"Fallback player dataset not found at {self.fallback_path}")

        with open(self.fallback_path, "r", encoding="utf-8") as f:
            raw_players = json.load(f)

        players = []
        for p in raw_players:
            st_dict = p.get("stats", {})
            st = PlayerStats(
                partite_a_voto=st_dict.get("partite_a_voto", 0),
                media_voto=st_dict.get("media_voto", 0.0),
                fantamedia=st_dict.get("fantamedia", 0.0),
                gol=st_dict.get("gol", 0),
                gol_subiti=st_dict.get("gol_subiti", 0),
                rigori_segnati=st_dict.get("rigori_segnati", 0),
                rigori_sbagliati=st_dict.get("rigori_sbagliati", 0),
                rigori_parati=st_dict.get("rigori_parati", 0),
                assist=st_dict.get("assist", 0),
                ammonizioni=st_dict.get("ammonizioni", 0),
                espulsioni=st_dict.get("espulsioni", 0),
                clean_sheets=st_dict.get("clean_sheets", 0),
                xg=st_dict.get("xg", p.get("xg", 0.0)),
                xa=st_dict.get("xa", p.get("xa", 0.0)),
                xg_90=st_dict.get("xg_90", p.get("xg_90", 0.0)),
                xa_90=st_dict.get("xa_90", p.get("xa_90", 0.0)),
                moneyball_index=st_dict.get("moneyball_index", p.get("moneyball_index", 0.0))
            )

            mb_data = compute_moneyball_metrics(
                ruolo=p["ruolo"],
                fvm_1000=p.get("fvm_1000", 1),
                prezzo_target=p.get("prezzo_target", 1),
                gol=st.gol,
                assist=st.assist,
                mv=p.get("mv", st.media_voto),
                fm=p.get("fm", st.fantamedia),
                piazzati=p.get("piazzati", ""),
                mod_rating=p.get("mod_rating", ""),
                clean_sheets=st.clean_sheets,
                gol_subiti=st.gol_subiti,
                existing_xg=st.xg,
                existing_xa=st.xa,
                existing_xg_90=st.xg_90,
                existing_xa_90=st.xa_90,
                existing_moneyball=st.moneyball_index
            )

            st.xg = mb_data["xg"]
            st.xa = mb_data["xa"]
            st.xg_90 = mb_data["xg_90"]
            st.xa_90 = mb_data["xa_90"]
            st.moneyball_index = mb_data["moneyball_index"]

            player = Player(
                id=p["id"],
                nome=p["nome"],
                squadra=p["squadra"],
                squadra_code=p["squadra_code"],
                ruolo=p["ruolo"],
                ruolo_mantra=p.get("ruolo_mantra", ""),
                qa=p.get("qa", 1),
                qi=p.get("qi", 1),
                fvm_1000=p.get("fvm_1000", 1),
                prezzo_target=p.get("prezzo_target", 1),
                prezzo_max=p.get("prezzo_max", 1),
                tier=p.get("tier", "Regolare"),
                piazzati=p.get("piazzati", ""),
                mod_rating=p.get("mod_rating", ""),
                mv=p.get("mv", 0.0),
                fm=p.get("fm", 0.0),
                xg=mb_data["xg"],
                xa=mb_data["xa"],
                xg_90=mb_data["xg_90"],
                xa_90=mb_data["xa_90"],
                moneyball_index=mb_data["moneyball_index"],
                note=p.get("note", ""),
                is_starter=p.get("is_starter", True),
                stats=st
            )
            players.append(player)

        return players
