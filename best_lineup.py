#!/usr/bin/env python3
"""
CLI Executable for Algoritmo 'Chi Schiero' - Fantacalcio 2026/2027.

Usage:
  python3 best_lineup.py
  python3 best_lineup.py --roster "Svilar, Dimarco, Bremer, Bellanova, Nico Paz, Calhanoglu, McTominay, Retegui, Malen, Thuram, Falcone"
  python3 best_lineup.py --roster data/sample_roster.json --giornata 1 --modificatore --json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.best_lineup import LineupOptimizer, get_best_lineup, VALID_FORMATIONS


def get_sample_fantasy_squad() -> List[Dict[str, Any]]:
    """Generates a standard 25-player realistic Serie A 2026/2027 fantasy squad."""
    return [
        # Portieri (3)
        {"nome": "Svilar", "squadra": "Roma", "ruolo": "P", "mv": 6.35, "fm": 5.45, "xg": 0.0, "xa": 0.0},
        {"nome": "Milinkovic-Savic", "squadra": "Torino", "ruolo": "P", "mv": 6.25, "fm": 5.20, "xg": 0.0, "xa": 0.0},
        {"nome": "Paleari", "squadra": "Torino", "ruolo": "P", "mv": 6.00, "fm": 5.00, "xg": 0.0, "xa": 0.0},
        # Difensori (8)
        {"nome": "Dimarco", "squadra": "Inter", "ruolo": "D", "mv": 6.45, "fm": 7.20, "xg": 4.5, "xa": 6.2},
        {"nome": "Theo Hernandez", "squadra": "Milan", "ruolo": "D", "mv": 6.35, "fm": 7.05, "xg": 4.0, "xa": 5.0},
        {"nome": "Bremer", "squadra": "Juventus", "ruolo": "D", "mv": 6.55, "fm": 6.80, "xg": 2.5, "xa": 1.0},
        {"nome": "Bastoni", "squadra": "Inter", "ruolo": "D", "mv": 6.40, "fm": 6.60, "xg": 1.8, "xa": 3.5},
        {"nome": "Buongiorno", "squadra": "Napoli", "ruolo": "D", "mv": 6.45, "fm": 6.60, "xg": 2.0, "xa": 0.5},
        {"nome": "Coco", "squadra": "Torino", "ruolo": "D", "mv": 6.35, "fm": 6.50, "xg": 2.2, "xa": 0.8},
        {"nome": "Beukema", "squadra": "Bologna", "ruolo": "D", "mv": 6.30, "fm": 6.35, "xg": 1.2, "xa": 0.4},
        {"nome": "Luperto", "squadra": "Cagliari", "ruolo": "D", "mv": 6.15, "fm": 6.15, "xg": 0.8, "xa": 0.2, "infortunato": True},
        # Centrocampisti (8)
        {"nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", "mv": 6.50, "fm": 7.60, "xg": 8.5, "xa": 5.0},
        {"nome": "Pulisic", "squadra": "Milan", "ruolo": "C", "mv": 6.45, "fm": 7.55, "xg": 9.0, "xa": 6.5},
        {"nome": "Koopmeiners", "squadra": "Juventus", "ruolo": "C", "mv": 6.45, "fm": 7.50, "xg": 7.8, "xa": 5.5},
        {"nome": "Zaccagni", "squadra": "Lazio", "ruolo": "C", "mv": 6.40, "fm": 7.40, "xg": 7.5, "xa": 4.8},
        {"nome": "Man", "squadra": "Parma", "ruolo": "C", "mv": 6.40, "fm": 7.10, "xg": 6.5, "xa": 4.2},
        {"nome": "Nico Paz", "squadra": "Como", "ruolo": "C", "mv": 6.50, "fm": 7.00, "xg": 5.5, "xa": 5.8},
        {"nome": "Frendrup", "squadra": "Genoa", "ruolo": "C", "mv": 6.35, "fm": 6.35, "xg": 1.0, "xa": 1.5},
        {"nome": "Brescianini", "squadra": "Atalanta", "ruolo": "C", "mv": 6.25, "fm": 6.70, "xg": 4.0, "xa": 2.0, "squalificato": True},
        # Attaccanti (6)
        {"nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", "mv": 6.60, "fm": 8.80, "xg": 18.5, "xa": 4.5},
        {"nome": "Malen", "squadra": "Roma", "ruolo": "A", "mv": 6.55, "fm": 8.50, "xg": 17.0, "xa": 3.8},
        {"nome": "Retegui", "squadra": "Atalanta", "ruolo": "A", "mv": 6.45, "fm": 8.05, "xg": 14.2, "xa": 2.5},
        {"nome": "Lookman", "squadra": "Atalanta", "ruolo": "A", "mv": 6.50, "fm": 7.90, "xg": 12.5, "xa": 6.0},
        {"nome": "Castellanos", "squadra": "Lazio", "ruolo": "A", "mv": 6.35, "fm": 7.30, "xg": 10.5, "xa": 2.8},
        {"nome": "Bonny", "squadra": "Parma", "ruolo": "A", "mv": 6.30, "fm": 6.95, "xg": 7.5, "xa": 3.0}
    ]


def print_cli_output(result, matchday: int, use_modifier: bool):
    print("=" * 72)
    print(" ⚽  FANTA AI WAR ROOM 2026/2027 — 'CHI SCHIERO' OTTIMIZZATORE")
    print("=" * 72)
    print(f" 📅  Giornata Serie A:     {matchday}")
    print(f" 🛡️  Modificatore Difesa:   {'ATTIVO' if use_modifier else 'DISATTIVATO'}")
    print(f" 🏆  Modulo Ottimale:       {result.formation}")
    print(f" 📈  Punteggio Previsto:    {result.total_expected_score:.2f} Punti")
    if use_modifier and result.modificatore_bonus > 0:
        print(f" 🎁  Bonus Modificatore:    +{result.modificatore_bonus:.1f} Punti (Media Voto Difesa: {result.defense_average:.3f})")
    print("-" * 72)
    print(" 💡  ANALISI TATTICA:")
    print(f"     {result.tactical_rationale}")
    print("=" * 72)

    # 1. Starters Table
    print("\n 🟢  11 TITOLARI SCHIERATI:")
    print(f" {'R':2} | {'CALCIATORE':18} | {'SQUADRA':10} | {'AVVERSARIO / CONTESTO':26} | {'EXP PTS':7}")
    print("-" * 72)
    for p in result.starters:
        role_badge = f"[{p.ruolo}]"
        context_short = f"{'Casa' if p.is_home else 'Trasf'} vs {p.opponent[:10]} (Diff {p.fixture_difficulty})"
        print(f" {role_badge:3} | {p.nome[:18]:18} | {p.squadra[:10]:10} | {context_short:26} | {p.expected_score:5.2f} pt")

    # 2. Bench Table
    if result.bench:
        print("\n 🟡  PANCHINA ORDINATA (12 CALCIATORI):")
        print(f" {'#':2} | {'R':2} | {'CALCIATORE':18} | {'SQUADRA':10} | {'PROB':4} | {'EXP PTS':7}")
        print("-" * 72)
        for idx, p in enumerate(result.bench, 1):
            role_badge = f"[{p.ruolo}]"
            print(f" {idx:2} | {role_badge:3} | {p.nome[:18]:18} | {p.squadra[:10]:10} | {p.probabilita:3}% | {p.expected_score:5.2f} pt")

    # 3. Excluded Table
    if result.excluded:
        print("\n 🔴  INDISPONIBILI / ESCLUSI (INFORTUNI / SQUALIFICHE):")
        print(f" {'R':2} | {'CALCIATORE':18} | {'SQUADRA':10} | {'MOTIVAZIONE':30}")
        print("-" * 72)
        for p in result.excluded:
            role_badge = f"[{p.ruolo}]"
            reason = p.injury_reason or p.tactical_note or "Indisponibile"
            print(f" {role_badge:3} | {p.nome[:18]:18} | {p.squadra[:10]:10} | {reason:30}")

    # 4. Formations Comparison Table
    if result.all_formations_evaluated:
        print("\n 📊  CONFRONTO MODULI TATTICI:")
        print(f" {'MODULO':8} | {'STATO':12} | {'PUNTI BASE':10} | {'BONUS MOD':10} | {'TOTALE':8}")
        print("-" * 72)
        for f in result.all_formations_evaluated:
            status = "SELEZIONATO" if f["formation"] == result.formation else ("Eligibile" if f.get("eligible") else "Non valido")
            starters_sc = f"{f.get('starters_score', 0.0):.2f}" if f.get("eligible") else "-"
            mod_sc = f"+{f.get('mod_bonus', 0.0):.1f}" if f.get("eligible") and f.get("mod_bonus", 0.0) > 0 else "-"
            tot_sc = f"{f.get('total_score', 0.0):.2f}" if f.get("eligible") else "-"
            print(f" {f['formation']:8} | {status:12} | {starters_sc:10} | {mod_sc:10} | {tot_sc:8}")

    print("=" * 72 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Fantacalcio 2026/2027 Lineup Optimizer ('Chi Schiero')"
    )
    parser.add_argument(
        "--roster",
        type=str,
        default=None,
        help="Path to JSON/CSV file or comma-separated list of player names (default: 25-player sample squad)"
    )
    parser.add_argument(
        "--lineups",
        type=str,
        default="data/probabili_formazioni.json",
        help="Path to probabili formazioni JSON (default: data/probabili_formazioni.json)"
    )
    parser.add_argument(
        "--fixtures",
        type=str,
        default="data/calendario_serie_a.json",
        help="Path to calendar fixtures JSON (default: data/calendario_serie_a.json)"
    )
    parser.add_argument(
        "--modificatore",
        dest="modificatore",
        action="store_true",
        default=True,
        help="Enable Modificatore Difesa calculation (default: True)"
    )
    parser.add_argument(
        "--no-modificatore",
        dest="modificatore",
        action="store_false",
        help="Disable Modificatore Difesa calculation"
    )
    parser.add_argument(
        "--giornata",
        type=int,
        default=1,
        help="Matchday number to optimize for (default: 1)"
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output results in JSON format"
    )

    args = parser.parse_args()

    roster_input = args.roster if args.roster else get_sample_fantasy_squad()

    try:
        optimizer = LineupOptimizer(
            lineups_path=args.lineups,
            fixtures_path=args.fixtures
        )
        result = optimizer.optimize_lineup(
            roster_input=roster_input,
            matchday=args.giornata,
            use_modifier=args.modificatore
        )

        if args.as_json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print_cli_output(result, matchday=args.giornata, use_modifier=args.modificatore)

    except Exception as e:
        if args.as_json:
            print(json.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"❌ Errore: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
