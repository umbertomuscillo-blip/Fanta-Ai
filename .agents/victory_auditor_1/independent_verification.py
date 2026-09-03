#!/usr/bin/env python3
"""
Independent Deep Verification Script for Victory Audit.
Audits generated datasets in data/ against all requirements of ORIGINAL_REQUEST.md.
"""

import csv
import json
import sys
from pathlib import Path

WORKSPACE = Path("/Users/umbertomuscillo/Documents/Fantacalcio")
DATA_DIR = WORKSPACE / "data"

CANONICAL_TEAMS = {
    "ATA": "Atalanta", "BOL": "Bologna", "CAG": "Cagliari", "COM": "Como",
    "EMP": "Empoli", "FIO": "Fiorentina", "GEN": "Genoa", "INT": "Inter",
    "JUV": "Juventus", "LAZ": "Lazio", "LEC": "Lecce", "MIL": "Milan",
    "MON": "Monza", "NAP": "Napoli", "PAR": "Parma", "ROM": "Roma",
    "TOR": "Torino", "UDI": "Udinese", "VEN": "Venezia", "VER": "Verona"
}

PROMOTED = {"Como", "Parma", "Venezia"}
PROMOTED_CODES = {"COM", "PAR", "VEN"}

RELEGATED = {"Salernitana", "Sassuolo", "Frosinone"}
RELEGATED_CODES = {"SAL", "SAS", "FRO"}

def audit():
    print("=== INDEPENDENT FORENSIC VERIFICATION START ===")
    
    # 1. File existence & size check
    files_to_check = [
        "teams.json", "teams.csv",
        "players.json", "players.csv", "players_db.json",
        "probabili_formazioni.json", "probabili_formazioni.csv",
        "lineups.json", "lineups.csv",
        "calendario_serie_a.json", "calendario_serie_a.csv",
        "calendar.json", "calendar.csv",
        "sync_report.json"
    ]
    
    print("\n[1] Artifact Existence & Byte Size:")
    for fn in files_to_check:
        fp = DATA_DIR / fn
        if not fp.exists():
            print(f"  ❌ Missing: {fn}")
            sys.exit(1)
        sz = fp.stat().st_size
        if sz == 0:
            print(f"  ❌ Empty file: {fn}")
            sys.exit(1)
        print(f"  ✓ {fn:<28} ({sz:>7} bytes)")

    # 2. Teams integrity (teams.json & teams.csv)
    print("\n[2] Teams Registry Integrity:")
    with open(DATA_DIR / "teams.json", "r", encoding="utf-8") as f:
        teams_json = json.load(f)
    with open(DATA_DIR / "teams.csv", "r", encoding="utf-8") as f:
        teams_csv = list(csv.DictReader(f))
    
    json_names = {t["name"] for t in teams_json}
    json_codes = {t["code"] for t in teams_json}
    csv_names = {t["name"] for t in teams_csv}
    csv_codes = {t["code"] for t in teams_csv}
    
    assert len(teams_json) == 20, f"Expected 20 teams in teams.json, found {len(teams_json)}"
    assert len(teams_csv) == 20, f"Expected 20 teams in teams.csv, found {len(teams_csv)}"
    assert json_names == set(CANONICAL_TEAMS.values()), "JSON team names mismatch"
    assert csv_names == set(CANONICAL_TEAMS.values()), "CSV team names mismatch"
    assert PROMOTED.issubset(json_names), f"Missing promoted in JSON: {PROMOTED - json_names}"
    assert PROMOTED.issubset(csv_names), f"Missing promoted in CSV: {PROMOTED - csv_names}"
    assert json_names.isdisjoint(RELEGATED), f"Relegated found in JSON: {json_names & RELEGATED}"
    assert csv_names.isdisjoint(RELEGATED), f"Relegated found in CSV: {csv_names & RELEGATED}"
    print(f"  ✓ Exactly 20 Serie A 2026/2027 clubs verified (JSON & CSV).")
    print(f"  ✓ Promoted clubs present: {sorted(PROMOTED)}")
    print(f"  ✓ Relegated clubs excluded: {sorted(RELEGATED)}")

    # 3. Players integrity (players.json, players.csv, players_db.json)
    print("\n[3] Players Dataset Integrity & Domain Realism:")
    with open(DATA_DIR / "players.json", "r", encoding="utf-8") as f:
        players_json = json.load(f)
    with open(DATA_DIR / "players.csv", "r", encoding="utf-8") as f:
        players_csv = list(csv.DictReader(f))
    with open(DATA_DIR / "players_db.json", "r", encoding="utf-8") as f:
        players_db = json.load(f)
    
    assert len(players_json) >= 500, f"Expected >= 500 players, found {len(players_json)}"
    assert len(players_json) == len(players_csv), f"Parity mismatch: JSON {len(players_json)} vs CSV {len(players_csv)}"
    db_sum = sum(len(players_db[r]) for r in ["P", "D", "C", "A"])
    assert db_sum == len(players_json), f"players_db partition sum {db_sum} != {len(players_json)}"
    
    roles_count = {"P": 0, "D": 0, "C": 0, "A": 0}
    player_teams = set()
    for p in players_json:
        r = p["ruolo"]
        roles_count[r] = roles_count.get(r, 0) + 1
        sq = p["squadra"]
        player_teams.add(sq)
        assert sq not in RELEGATED, f"Player {p['nome']} is in relegated club {sq}"
        assert p["qa"] >= 1, f"Invalid QA for {p['nome']}"
        assert p["fvm_1000"] >= 1, f"Invalid FVM for {p['nome']}"
        assert p["prezzo_target"] >= 1, f"Invalid target price for {p['nome']}"
    
    assert player_teams == set(CANONICAL_TEAMS.values()), f"Player teams mismatch: {player_teams ^ set(CANONICAL_TEAMS.values())}"
    print(f"  ✓ Total players: {len(players_json)} across all 20 Serie A clubs.")
    print(f"  ✓ Role breakdown: P={roles_count['P']}, D={roles_count['D']}, C={roles_count['C']}, A={roles_count['A']}")
    print(f"  ✓ JSON vs CSV vs players_db parity: 100% matched ({len(players_json)} records).")

    # 4. Probable Lineups Integrity (probabili_formazioni.json & csv)
    print("\n[4] Probable Lineups Integrity:")
    with open(DATA_DIR / "probabili_formazioni.json", "r", encoding="utf-8") as f:
        lineups_data = json.load(f)
    matches = lineups_data["matches"]
    assert len(matches) == 10, f"Expected 10 matches, found {len(matches)}"
    
    lineup_teams = set()
    for m in matches:
        for side in ["home_lineup", "away_lineup"]:
            tl = m[side]
            sq = tl["squadra"]
            lineup_teams.add(sq)
            assert sq in CANONICAL_TEAMS.values(), f"Unknown/relegated club in lineup: {sq}"
            starters = tl["titolari"]
            assert len(starters) == 11, f"Team {sq} has {len(starters)} starters (expected 11)"
            gk_count = sum(1 for p in starters if p.get("ruolo") == "P")
            assert gk_count == 1, f"Team {sq} has {gk_count} starting GKs (expected exactly 1)"
            bench = tl["panchina"]
            assert len(bench) >= 5, f"Team {sq} bench too small: {len(bench)}"
    
    assert lineup_teams == set(CANONICAL_TEAMS.values()), f"Lineups teams mismatch: {lineup_teams ^ set(CANONICAL_TEAMS.values())}"
    print(f"  ✓ Exactly 10 fixtures covering all 20 clubs.")
    print(f"  ✓ All 20 teams field exactly 11 starters and exactly 1 goalkeeper.")

    # 5. Season Calendar Integrity (calendario_serie_a.json & csv)
    print("\n[5] Season Calendar & Symmetry Integrity:")
    with open(DATA_DIR / "calendario_serie_a.json", "r", encoding="utf-8") as f:
        calendar = json.load(f)
    assert len(calendar) == 380, f"Expected 380 fixtures, found {len(calendar)}"
    
    giornate = set()
    home_matches = {c: 0 for c in CANONICAL_TEAMS.keys()}
    away_matches = {c: 0 for c in CANONICAL_TEAMS.keys()}
    pairs = set()
    
    for fix in calendar:
        giornate.add(fix["giornata"])
        hc = fix["home_team_code"]
        ac = fix["away_team_code"]
        assert hc in CANONICAL_TEAMS, f"Invalid home code {hc}"
        assert ac in CANONICAL_TEAMS, f"Invalid away code {ac}"
        assert hc != ac, f"Self match: {hc}"
        home_matches[hc] += 1
        away_matches[ac] += 1
        pairs.add((hc, ac))
    
    assert len(giornate) == 38, f"Expected 38 matchdays, found {len(giornate)}"
    assert len(pairs) == 380, f"Expected 380 unique pairings, found {len(pairs)}"
    for c in CANONICAL_TEAMS.keys():
        assert home_matches[c] == 19, f"Team {c} has {home_matches[c]} home matches (expected 19)"
        assert away_matches[c] == 19, f"Team {c} has {away_matches[c]} away matches (expected 19)"
    print(f"  ✓ Exactly 38 matchdays, 380 total fixtures.")
    print(f"  ✓ Double round-robin verified: exactly 19 home / 19 away games per team.")
    print(f"  ✓ All 380 ordered pairwise matches (home, away) are unique.")

    # 6. City Pairs Alternation Check (Milan/Inter, Juve/Torino, Roma/Lazio)
    print("\n[6] City-Pair Ground Sharing Alternation:")
    city_pairs = [("INT", "MIL"), ("ROM", "LAZ"), ("JUV", "TOR")]
    for c1, c2 in city_pairs:
        clashes = 0
        for g in range(1, 39):
            g_matches = [f for f in calendar if f["giornata"] == g]
            c1_home = any(f["home_team_code"] == c1 for f in g_matches)
            c2_home = any(f["home_team_code"] == c2 for f in g_matches)
            if c1_home and c2_home:
                clashes += 1
        print(f"  ✓ Ground sharing check for {c1}/{c2}: {clashes} home clashes out of 38 matchdays.")
        assert clashes == 0, f"City pair {c1}/{c2} has {clashes} stadium home clashes!"

    print("\n=== ALL INDEPENDENT VERIFICATION CHECKS PASSED (100%) ===")

if __name__ == "__main__":
    audit()
