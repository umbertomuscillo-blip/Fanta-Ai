#!/usr/bin/env python3
"""
Adversarial Domain Stress Harness for Fantacalcio 2026/2027
Author: Challenger 2 (Empirical Challenger & Domain Critic)
"""

import json
import csv
import sys
import html
from pathlib import Path

DATA_DIR = Path("/Users/umbertomuscillo/Documents/Fantacalcio/data")

def run_adversarial_tests():
    print("=" * 70)
    print("STARTING ADVERSARIAL DOMAIN STRESS TESTS")
    print("=" * 70)

    # 1. Load data
    with open(DATA_DIR / "players.json", "r", encoding="utf-8") as f:
        players = json.load(f)
    with open(DATA_DIR / "probabili_formazioni.json", "r", encoding="utf-8") as f:
        lineups = json.load(f)
    with open(DATA_DIR / "calendario_serie_a.json", "r", encoding="utf-8") as f:
        calendar = json.load(f)

    errors = []

    # Check 1: Starters and bench overlap in the same team
    matches = lineups.get("matches", []) if isinstance(lineups, dict) else lineups
    for m in matches:
        for side in ["home_lineup", "away_lineup"]:
            tdata = m.get(side, {})
            sq = tdata.get("squadra")
            starters = {p["nome"] for p in tdata.get("titolari", [])}
            bench = {p["nome"] for p in tdata.get("panchina", [])}
            overlap = starters.intersection(bench)
            if overlap:
                errors.append(f"Team {sq} has players in both starting XI and bench: {overlap}")

    print(f"[Check 1] Starter & Bench Disjointness: {'PASS' if not any('both starting XI' in e for e in errors) else 'FAIL'}")

    # Check 2: Player ID uniqueness
    pids = [p["id"] for p in players]
    if len(pids) != len(set(pids)):
        dup_ids = [pid for pid in pids if pids.count(pid) > 1]
        errors.append(f"Duplicate player IDs found: {set(dup_ids)}")
    print(f"[Check 2] Player ID Uniqueness: {'PASS' if not any('Duplicate player IDs' in e for e in errors) else 'FAIL'}")

    # Check 3: Minimum / Maximum price sanity
    invalid_prices = [p for p in players if p.get("prezzo_target", 0) < 1 or p.get("qa", 0) < 1]
    if invalid_prices:
        errors.append(f"Found {len(invalid_prices)} players with invalid prices (< 1)")
    print(f"[Check 3] Price Non-Negativity & Lower Bound: {'PASS' if not any('invalid prices' in e for e in errors) else 'FAIL'}")

    # Check 4: City Rival Pairing Complementarity (San Siro: Inter & Milan, Olimpico: Roma & Lazio, Torino: Juve & Toro)
    # They should never both play at home on the exact same matchday (except derby)
    rival_pairs = [("Inter", "Milan"), ("Roma", "Lazio"), ("Juventus", "Torino")]
    giornate_fixtures = {}
    for fix in calendar:
        g = fix.get("giornata")
        giornate_fixtures.setdefault(g, []).append(fix)

    for team1, team2 in rival_pairs:
        conflicts = 0
        for g, flist in giornate_fixtures.items():
            home_teams = {f.get("home_team") or f.get("squadra_casa") for f in flist}
            if team1 in home_teams and team2 in home_teams:
                # Check if it's the derby
                derby = any(
                    (f.get("home_team") == team1 and f.get("away_team") == team2) or
                    (f.get("home_team") == team2 and f.get("away_team") == team1)
                    for f in flist
                )
                if not derby:
                    conflicts += 1
        print(f"[Check 4] Stadium Schedule Complementarity ({team1} & {team2}): {38 - conflicts}/38 matchdays perfectly alternating")

    # Check 5: Modificatore Difesa rating consistency
    mod_ratings = {p.get("mod_rating") for p in players if p.get("ruolo") == "D"}
    expected_mod_ratings = {"", "DIVINO", "SUPER", "TOP", "OTTIMO", "BUONO", "DISCRETO"}
    unknown_mod = mod_ratings - expected_mod_ratings
    if unknown_mod:
        errors.append(f"Unknown modifier ratings: {unknown_mod}")
    print(f"[Check 5] Defense Modifier Ratings Taxonomy: {'PASS' if not unknown_mod else 'FAIL'}")

    # Check 6: Probable lineups starters have corresponding records in players list
    all_player_names = {html.unescape(p["nome"]).lower() for p in players}
    missing_lineup_players = []
    for m in matches:
        for side in ["home_lineup", "away_lineup"]:
            tdata = m.get(side, {})
            for starter in tdata.get("titolari", []):
                sname = html.unescape(starter["nome"]).lower()
                if sname not in all_player_names:
                    # check substring
                    if not any(sname in p or p in sname for p in all_player_names):
                        missing_lineup_players.append(f"{tdata.get('squadra')}: {starter['nome']}")

    print(f"[Check 6] Lineup Starters Referential Integrity: {'PASS' if len(missing_lineup_players) == 0 else f'WARN ({len(missing_lineup_players)} missing)'}")
    if missing_lineup_players:
        print(f"         Missing starters: {missing_lineup_players[:5]}")

    print("=" * 70)
    print(f"ADVERSARIAL STRESS TEST SUMMARY: {len(errors)} critical errors encountered")
    print("=" * 70)
    return len(errors) == 0

if __name__ == "__main__":
    success = run_adversarial_tests()
    sys.exit(0 if success else 1)
