"""Parsers package for extracting and structuring Fantacalcio data."""
from .players_parser import PlayersParser
from .lineups_parser import LineupsParser
from .fixtures_parser import FixturesParser

__all__ = ["PlayersParser", "LineupsParser", "FixturesParser"]
