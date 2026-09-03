"""
Parser for Serie A 2026/2027 Calendar and Fixtures.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.config import FALLBACK_DIR, normalize_team
from src.models import MatchFixture

logger = logging.getLogger(__name__)

TOP_TIER_TEAMS = {"Inter", "Juventus", "Milan", "Napoli", "Atalanta"}
MID_TIER_TEAMS = {"Roma", "Lazio", "Fiorentina", "Bologna", "Torino"}


def _compute_gk_difficulty(opponent: str) -> int:
    if opponent in TOP_TIER_TEAMS:
        return 3
    if opponent in MID_TIER_TEAMS:
        return 2
    return 1


class FixturesParser:
    def __init__(self, fallback_path: Optional[Path] = None):
        self.fallback_path = fallback_path or (FALLBACK_DIR / "fallback_calendar.json")

    def parse(self, fixtures_text: Optional[str] = None) -> List[MatchFixture]:
        """
        Parses 38 matchdays / 380 matches from OpenFootball plaintext.
        Falls back to high-fidelity bundled fallback if text is missing or invalid.
        """
        if fixtures_text:
            try:
                fixtures = self._parse_from_text(fixtures_text)
                if len(fixtures) == 380:
                    logger.info(f"Successfully parsed all 380 Serie A 2026/2027 fixtures from plaintext.")
                    return fixtures
                logger.warning(f"Parsed {len(fixtures)} fixtures from text (<380 threshold). Falling back to bundled dataset.")
            except Exception as e:
                logger.warning(f"Error parsing fixtures text: {e}. Falling back to bundled dataset.")

        return self._load_fallback()

    def _parse_from_text(self, text: str) -> List[MatchFixture]:
        matchday_blocks = re.split(r'▪\s*Matchday\s+(\d+)', text)
        if len(matchday_blocks) < 3:
            return []

        fixtures: List[MatchFixture] = []

        for i in range(1, len(matchday_blocks), 2):
            m_day = int(matchday_blocks[i])
            block_txt = matchday_blocks[i + 1]

            current_date = "2026-08-22"
            for line in block_txt.splitlines():
                line = line.strip()
                if not line:
                    continue

                if re.match(r'^[A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d+', line):
                    current_date = line
                    continue

                m_match = re.search(r'(?:(\d{1,2}:\d{2})\s+)?(.*?)\s+v\s+(.*?)(?:\s+(\d+-\d+(?:\s+\([^)]+\))?))?$', line)
                if m_match:
                    time_str = m_match.group(1) or "15:00"
                    home_raw = m_match.group(2).strip()
                    away_raw = m_match.group(3).strip()
                    score_str = m_match.group(4) or ""

                    try:
                        home_name, home_code = normalize_team(home_raw)
                        away_name, away_code = normalize_team(away_raw)
                    except Exception as e:
                        logger.debug(f"Skipping unparseable team pair '{home_raw}' vs '{away_raw}': {e}")
                        continue

                    home_score = None
                    away_score = None
                    status = "SCHEDULED"

                    if score_str:
                        m_sc = re.match(r'^(\d+)-(\d+)', score_str)
                        if m_sc:
                            home_score = int(m_sc.group(1))
                            away_score = int(m_sc.group(2))
                            status = "FINISHED"

                    mid = f"2026_G{m_day:02d}_{home_code}_{away_code}"
                    fixture = MatchFixture(
                        match_id=mid,
                        giornata=m_day,
                        date_str=f"{current_date} {time_str}",
                        home_team=home_name,
                        home_team_code=home_code,
                        away_team=away_name,
                        away_team_code=away_code,
                        home_score=home_score,
                        away_score=away_score,
                        status=status,
                        difficolta_portieri={
                            home_name: _compute_gk_difficulty(away_name),
                            away_name: _compute_gk_difficulty(home_name)
                        },
                        season="2026/2027"
                    )
                    fixtures.append(fixture)

        return fixtures

    def _load_fallback(self) -> List[MatchFixture]:
        """Loads fixtures from high-fidelity fallback dataset."""
        logger.info(f"Loading fallback calendar from {self.fallback_path}")
        if not self.fallback_path.exists():
            raise FileNotFoundError(f"Fallback calendar dataset not found at {self.fallback_path}")

        with open(self.fallback_path, "r", encoding="utf-8") as f:
            raw_fixtures = json.load(f)

        fixtures = []
        for f in raw_fixtures:
            fixture = MatchFixture(
                match_id=f["match_id"],
                giornata=f["giornata"],
                date_str=f.get("date_str", ""),
                home_team=f["home_team"],
                home_team_code=f["home_team_code"],
                away_team=f["away_team"],
                away_team_code=f["away_team_code"],
                home_score=f.get("home_score"),
                away_score=f.get("away_score"),
                status=f.get("status", "SCHEDULED"),
                difficolta_portieri=f.get("difficolta_portieri", {}),
                season=f.get("season", "2026/2027")
            )
            fixtures.append(fixture)

        return fixtures
