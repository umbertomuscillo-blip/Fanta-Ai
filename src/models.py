"""
Data models for Fantacalcio 2026/2027 Pipeline.
Defines strongly typed dataclasses and serialization protocols for all entities.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime


@dataclass
class PlayerStats:
    partite_a_voto: int = 0
    media_voto: float = 0.0
    fantamedia: float = 0.0
    gol: int = 0
    gol_subiti: int = 0
    rigori_segnati: int = 0
    rigori_sbagliati: int = 0
    rigori_parati: int = 0
    assist: int = 0
    ammonizioni: int = 0
    espulsioni: int = 0
    clean_sheets: int = 0
    xg: float = 0.0
    xa: float = 0.0
    xg_90: float = 0.0
    xa_90: float = 0.0
    moneyball_index: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Player:
    id: int
    nome: str
    squadra: str
    squadra_code: str
    ruolo: str
    ruolo_mantra: str = ""
    qa: int = 1
    qi: int = 1
    fvm_1000: int = 1
    prezzo_target: int = 1
    prezzo_max: int = 1
    tier: str = "Regolare"
    piazzati: str = ""
    mod_rating: str = ""
    mv: float = 0.0
    fm: float = 0.0
    note: str = ""
    is_starter: bool = True
    xg: float = 0.0
    xa: float = 0.0
    xg_90: float = 0.0
    xa_90: float = 0.0
    moneyball_index: float = 0.0
    stats: PlayerStats = field(default_factory=PlayerStats)
    updated_at: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["stats"] = self.stats.to_dict() if isinstance(self.stats, PlayerStats) else self.stats
        return d

    def to_csv_dict(self) -> dict[str, Any]:
        st = self.stats if isinstance(self.stats, dict) else self.stats.to_dict()
        return {
            "id": self.id,
            "nome": self.nome,
            "squadra": self.squadra,
            "squadra_code": self.squadra_code,
            "ruolo": self.ruolo,
            "ruolo_mantra": self.ruolo_mantra,
            "qa": self.qa,
            "qi": self.qi,
            "fvm_1000": self.fvm_1000,
            "prezzo_target": self.prezzo_target,
            "prezzo_max": self.prezzo_max,
            "tier": self.tier,
            "piazzati": self.piazzati,
            "mod_rating": self.mod_rating,
            "presenze": st.get("partite_a_voto", 0),
            "media_voto": self.mv or st.get("media_voto", 0.0),
            "fantamedia": self.fm or st.get("fantamedia", 0.0),
            "gol": st.get("gol", 0),
            "gol_subiti": st.get("gol_subiti", 0),
            "rigori_segnati": st.get("rigori_segnati", 0),
            "rigori_sbagliati": st.get("rigori_sbagliati", 0),
            "rigori_parati": st.get("rigori_parati", 0),
            "assist": st.get("assist", 0),
            "ammonizioni": st.get("ammonizioni", 0),
            "espulsioni": st.get("espulsioni", 0),
            "clean_sheets": st.get("clean_sheets", 0),
            "xg": self.xg if self.xg != 0.0 else st.get("xg", 0.0),
            "xa": self.xa if self.xa != 0.0 else st.get("xa", 0.0),
            "xg_90": self.xg_90 if self.xg_90 != 0.0 else st.get("xg_90", 0.0),
            "xa_90": self.xa_90 if self.xa_90 != 0.0 else st.get("xa_90", 0.0),
            "moneyball_index": self.moneyball_index if self.moneyball_index != 0.0 else st.get("moneyball_index", 0.0),
            "titolare_probabile": self.is_starter,
            "note": self.note,
            "updated_at": self.updated_at
        }


@dataclass
class TeamLineup:
    squadra: str
    squadra_code: str
    modulo: str
    titolari: list[dict[str, Any]] = field(default_factory=list)
    panchina: list[dict[str, Any]] = field(default_factory=list)
    ballottaggi: list[dict[str, Any]] = field(default_factory=list)
    infortunati: list[dict[str, Any]] = field(default_factory=list)
    squalificati: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatchLineup:
    match_id: str
    giornata: int
    home_team: str
    home_team_code: str
    away_team: str
    away_team_code: str
    date_str: str = ""
    stadium: str = ""
    home_lineup: Optional[TeamLineup] = None
    away_lineup: Optional[TeamLineup] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "giornata": self.giornata,
            "date_str": self.date_str,
            "stadium": self.stadium,
            "home_team": self.home_team,
            "home_team_code": self.home_team_code,
            "away_team": self.away_team,
            "away_team_code": self.away_team_code,
            "home_lineup": self.home_lineup.to_dict() if self.home_lineup else {},
            "away_lineup": self.away_lineup.to_dict() if self.away_lineup else {}
        }


@dataclass
class MatchFixture:
    match_id: str
    giornata: int
    date_str: str
    home_team: str
    home_team_code: str
    away_team: str
    away_team_code: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str = "SCHEDULED"
    difficolta_portieri: dict[str, int] = field(default_factory=dict)
    season: str = "2026/2027"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_csv_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "giornata": self.giornata,
            "season": self.season,
            "date_str": self.date_str,
            "home_team": self.home_team,
            "home_team_code": self.home_team_code,
            "away_team": self.away_team,
            "away_team_code": self.away_team_code,
            "home_score": self.home_score if self.home_score is not None else "",
            "away_score": self.away_score if self.away_score is not None else "",
            "status": self.status,
            "difficolta_home": self.difficolta_portieri.get(self.home_team, 2),
            "difficolta_away": self.difficolta_portieri.get(self.away_team, 2)
        }


@dataclass
class Team:
    id: str
    code: str
    name: str
    full_name: str
    city: str
    stadium: str
    coach: str
    promoted: bool
    primary_color: str
    secondary_color: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SyncReport:
    timestamp: str
    success: bool
    players_count: int
    lineups_count: int
    fixtures_count: int
    teams_count: int
    execution_time_sec: float
    errors: list[str] = field(default_factory=list)
    source_tiers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
