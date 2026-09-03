# Handoff Report — Data Architecture, Pipeline & Test Fixtures
**Agent**: `survey_source_explorer`  
**Milestone**: M1 - Survey & Source Discovery / Data Schema & Fixture Design  
**Date**: 2026-09-02  

---

## 1. Observation

1. **Root Configuration & Requirements**:
   - `ORIGINAL_REQUEST.md` (lines 1-74) specifies:
     - Baseline pipeline requirements: manual update script `update_fanta_data.py`, autonomous source selection, structured data in `data/`, strict Serie A 2026/2027 club validation (Como, Parma, Venezia in; Salernitana, Sassuolo, Frosinone out).
     - Advanced feature requirements:
       - R1: Calcolatore Prezzo Massimo (Frontend JS widget in `dashboard/index.html` calculating max bid from user budget, opponent credits, and remaining slots).
       - R2: Algoritmo "Chi Schiero" (Backend Python `best_lineup.py` evaluating `lineups.json`, goalkeeper grid, best 11 starters, valid formations, defense modifier).
       - R3: Indice Moneyball (Expected Goals - xG, Expected Assists - xA, Moneyball Index integrated into JSON datasets).
2. **Storage Structure in `data/`**:
   - `data/players.json` (20,582 lines, 434,303 bytes): flat array of 588 player objects containing `id`, `nome`, `squadra`, `squadra_code`, `ruolo` (`P`, `D`, `C`, `A`), `ruolo_mantra`, `qa`, `qi`, `fvm_1000`, `prezzo_target`, `prezzo_max`, `tier`, `piazzati`, `mod_rating`, `mv`, `fm`, `note`, `is_starter`, `stats` (12 counters), `updated_at`.
   - `data/players_db.json` (434,355 bytes): grouped by role key (`{"P": [...], "D": [...], "C": [...], "A": [...]}`) consumed by `dashboard/index.html`.
   - `data/lineups.json` / `data/probabili_formazioni.json` (3,214 lines, 77,275 bytes): 10 matches for Matchday 1, 20 teams with exact 11 `titolari` each, plus `panchina`, `ballottaggi`, `infortunati`, `squalificati`.
   - `data/calendar.json` / `data/calendario_serie_a.json` (6,462 lines, 146,944 bytes): 38 matchdays, 380 total fixtures, each with `difficolta_portieri` (1 = Easy, 2 = Medium, 3 = Hard).
   - `data/teams.json` (242 lines, 5,759 bytes): 20 Serie A 2026/2027 clubs including Como (`COM`), Parma (`PAR`), Venezia (`VEN`).
   - `data/sync_report.json` (315 bytes): execution status, timestamp, entity counts, source tiers, errors.
3. **Pipeline Ingestion & Execution**:
   - `update_fanta_data.py` (lines 1-130): master CLI script accepting `--all`, `--players`, `--lineups`, `--fixtures`, `--offline-fallback`, `-v`/`--verbose`.
   - `src/pipeline.py` (lines 1-170): coordinates `PlayersFetcher`/`Parser`, `LineupsFetcher`/`Parser`, `FixturesFetcher`/`Parser`, `SeasonValidator`, and `JsonExporter`/`CsvExporter`.
   - 3-tier fallback architecture: Tier 1 (Live HTTP) -> Tier 2 (`data/cache/`) -> Tier 3 (`src/fallback_data/`).
4. **Dashboard & UI Structure**:
   - `dashboard/index.html` (lines 1-664): contains live tabs for "Matrice Incroci Portieri 2026/27", "Listone Ufficiale (588 Calciatori Reali)", "Live Auction & Rival Tracker", and "Calcolatore Modificatore (+1 a +6)".
   - Script logic (lines 536-660) currently tracks `userRoster` (`{P: [], D: [], C: [], A: []}`), limits (P: 3, D: 8, C: 8, A: 6), remaining credits (`totalBudget - userTotalSpent`), and basic `maxBid = remainingCredits - (remainingSlots - 1)`.

---

## 2. Logic Chain

1. From **Observation 1 & 2**: All core entity datasets (`players.json`, `lineups.json`, `calendar.json`, `teams.json`, `players_db.json`) are already generated, validated against Serie A 2026/2027 invariants, and stored in standard JSON/CSV format.
2. From **Observation 2 & 4**: To implement R1 (Max Bid Calculator) in `dashboard/index.html`, the existing JS roster and rival tracker functions (`buyPlayer`, `spendRival`, `updateRosterUI`) can be extended with role-specific constraints, dynamic rival ceiling thresholding, and live strategic recommendations.
3. From **Observation 2 & 3**: To implement R2 (`best_lineup.py`), the optimizer must load `data/lineups.json` (for starter probability and status), `data/players.json` (for FM, MV, role, tier, penalties), and `data/calendar.json` (for goalkeeper difficulty matrix and home/away status), test all 7 valid formations (3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1), and calculate expected score including defense modifier bonus.
4. From **Observation 2 & 3**: To implement R3 (Moneyball Index), `PlayerStats` in `src/models.py`, `src/parsers/players_parser.py`, and `src/storage/json_exporter.py` should be enriched with `xg`, `xa`, `xg_90`, `xa_90`, and `moneyball_index` without breaking the existing schema or `dashboard/index.html`.
5. From **Observation 1, 2 & 4**: Realistic mock user rosters (balanced meta, budget attack heavy, edge-case injury squad) provide end-to-end test fixtures for automated test suites (`test_lineup_logic.py`, `test_moneyball.py`, `test_max_bid.py`).

---

## 3. Caveats

1. **Live Scraping Rate Limits**: While Tier 1 live HTTP endpoints on `fantacalcio.it` and `openfootball` are functional, offline test executions should use `--offline-fallback` or mocked fixtures to ensure fast and non-flaky test runs.
2. **xG/xA Data Granularity**: Early season matchday sample sizes (e.g. Giornate 1-2) produce low cumulative xG/xA; the Moneyball formula therefore incorporates per-90 rates and historical fantamedia weighting to maintain robust player rankings.
3. **No other caveats**: The schema contracts and fixtures are fully backwards-compatible.

---

## 4. Conclusion

1. The data layer in `data/` is complete, structurally sound, and conforms 100% to Serie A 2026/2027 requirements.
2. Concrete schemas, mathematical models, mock user rosters, and test blueprints have been formalized in `.agents/survey_source_explorer/analysis.md`.
3. The downstream implementation workers have unambiguous interface contracts for R1 (Frontend Max Bid), R2 (Backend `best_lineup.py`), and R3 (Moneyball Index).

---

## 5. Verification Method

To independently verify all findings and datasets:

1. **Pipeline Execution & Invariant Verification**:
   ```bash
   python3 update_fanta_data.py --all --offline-fallback
   python3 test_data_integrity.py
   ```
   *Expected outcome*: Exit code 0, all 10 files present in `data/`, 20 clubs verified (Como, Parma, Venezia present; Salernitana, Sassuolo, Frosinone absent), 588+ players, 10 lineups, 380 calendar fixtures.

2. **Full Test Suite Verification**:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
   *Expected outcome*: 100% tests passing across all tiers (Feature coverage, Boundary/Corner, Combinations, Real-World).

3. **Schema & Analysis Inspection**:
   - Inspect `.agents/survey_source_explorer/analysis.md` for complete schema specifications and mock rosters.
