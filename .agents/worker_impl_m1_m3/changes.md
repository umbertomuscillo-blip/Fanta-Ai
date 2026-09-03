# Changes Summary — Advanced Fantacalcio Suite (R1, R2, R3)

## 1. R1: Frontend Calcolatore Prezzo Massimo & Strategia Asta (`dashboard/index.html`)
- Added real-time Max Bid calculation metrics to the header bar and the Live Auction tab:
  * Absolute User Max Single Bid: $C_{user} - (S_{user} - 1)$
  * Top Rival Single-Bid Ceiling: $\max_i (C_{rival,i} - (S_{rival,i} - 1))$ with rival identification
  * Mathematical Winning Threshold: $(\text{Top Rival Max Bid} + 1)$
  * Role-based safety reserves ($P_{rem}, D_{rem}, C_{rem}, A_{rem}$) ensuring 1 cr minimum per slot.
- Implemented Live Interactive Player Auction Evaluator:
  * Dropdown/search of all 588 Serie A players with instant display of Role, Squad, Tier, Target Price (500 budget), Max Price, FVM, xG, xA, and Moneyball Index.
  * Real-time dynamic tactical advice badges: `COMPRA`, `RILANCIA`, `LASCIA`, `ATTENZIONE BUDGET` with contextual rationale based on price vs target vs rival ceiling vs safety reserve.
  * Quick "+ Aggiudica & Aggiungi a Rosa" button syncing directly with user roster and budget balances.
- Enriched Listone table with Moneyball Index, xG/xA statistics, and "⚡ Valuta" shortcut.

## 2. R2: Algoritmo "Chi Schiero" (`src/best_lineup.py` and `best_lineup.py`)
- Created `src/best_lineup.py` with `LineupOptimizer` and `get_best_lineup` API:
  * Cross-references input squad with `data/players.json`, `data/probabili_formazioni.json` (probabilities, ballotaggi, infortunati, squalificati) and `data/calendario_serie_a.json` (difficulty tiers 1-3, home/away advantage).
  * Strict exclusion of injured and suspended players (0% probability or listed in infortunati/squalificati).
  * Evaluates all 7 valid Fantacalcio formations (3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1).
  * Evaluates Modificatore Difesa for $\ge 4$ defenders (GK + top 3 defenders expected MV average: $<6.0 \to 0$, $6.0-6.49 \to +1$, $6.5-6.99 \to +3$, $\ge 7.0 \to +6$).
  * Optimizes starting XI and builds 12-man ordered bench (P, D, C, A) with detailed tactical explanations.
- Created CLI entrypoint `best_lineup.py` supporting flags: `--roster`, `--lineups`, `--fixtures`, `--modificatore`, `--no-modificatore`, `--giornata`, `--json`, with default 25-man squad fallback.

## 3. R3: Indice Moneyball Backend & Data Pipelines
- Enriched `Player` and `PlayerStats` dataclasses in `src/models.py` with `xg: float = 0.0`, `xa: float = 0.0`, `xg_90: float = 0.0`, `xa_90: float = 0.0`, `moneyball_index: float = 0.0`.
- Implemented `compute_moneyball_metrics` in `src/parsers/players_parser.py` computing authentic expected goals, expected assists, per-90 rates, and performance-to-price Moneyball ratios.
- Updated `src/storage/json_exporter.py` and `src/storage/csv_exporter.py` to preserve full schema compatibility and include all Moneyball fields.
- Enriched `src/fallback_data/fallback_players.json` and `src/fallback_data/fallback_lineups.json` with authentic 2026/27 stats and injuries/suspensions.
- Updated all output datasets via `python3 update_fanta_data.py --all --offline-fallback`.

## 4. Test Suites Added & Passing
- `test_lineup_logic.py`: 7 unit tests covering formations, injuries/suspensions strict exclusion, Modificatore thresholds, CLI & JSON output.
- `tests/test_moneyball.py`: 5 unit tests covering models, algorithms, JSON/CSV integrity, and schema compatibility.
- Total test coverage: 133 automated tests passing cleanly with 100% success rate.
