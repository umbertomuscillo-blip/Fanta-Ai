"""Fetchers package for retrieving Fantacalcio and Serie A datasets."""
from .base_fetcher import BaseFetcher
from .players_fetcher import PlayersFetcher
from .lineups_fetcher import LineupsFetcher
from .fixtures_fetcher import FixturesFetcher

__all__ = ["BaseFetcher", "PlayersFetcher", "LineupsFetcher", "FixturesFetcher"]
