# Fantacalcio 2026/2027: Codebase Architecture & Integration Analysis

**Date**: 2026-09-02  
**Target Workspace**: `/Users/umbertomuscillo/Documents/Fantacalcio`  
**Explorer**: `survey_codebase_explorer`  
**Mission**: Comprehensive survey of the existing codebase to establish architecture, data schema, dashboard layout, and exact integration points for the 3 new requirements (Calcolatore Prezzo Massimo, Best Lineup engine, Moneyball Index).

---

## 1. Executive Summary & Codebase Architecture

The project is an automated, modular, zero-external-dependency Python ecosystem and HTML/JS frontend designed for Serie A 2026/2027 Fantacalcio management.

### Directory Structure & Layout
```
/Users/umbertomuscillo/Documents/Fantacalcio/
├── ORIGINAL_REQUEST.md          # Full history of user requests & requirements
├── PROJECT.md                   # Architectural principles, feature inventory & milestones
├── TEST_INFRA.md                # 5-tier test architecture definition
├── TEST_READY.md                # Test execution readiness report
├── update_fanta_data.py         # CLI executable entry point (--all, --players, --lineups, etc.)
├── test_data_integrity.py       # Acceptance test suite (8 tests)
├── dashboard/
│   └── index.html               # Frontend dashboard (Tailwind CSS, Portieri, Database, Live Auction, Modificatore)
├── data/
│   ├── cache/                   # Raw HTML snapshots (lineups, quotazioni, statistiche)
│   ├── players.json             # Flat JSON dataset (588+ active players)
│   ├── players.csv              # CSV dataset of players
│   ├── players_db.json          # Role-grouped JSON ({"P": [...], "D": [...], "C": [...], "A": [...]})
│   ├── probabili_formazioni.json# Probable matchday lineups (10 matches, 20 clubs)
│   ├── probabili_formazioni.csv # Probable lineups tabular CSV
│   ├── lineups.json & .csv      # Alias filenames for lineups
│   ├── calendario_serie_a.json  # 38 matchdays, 380 fixtures
│   ├── calendario_serie_a.csv   # Calendar tabular CSV
│   ├── calendar.json & .csv     # Alias filenames for calendar
│   ├── teams.json & teams.csv   # 20 Serie A 2026/27 clubs metadata
│   └── sync_report.json         # Pipeline run execution report
├── src/
│   ├── __init__.py
│   ├── config.py                # 20 clubs (incl. Como, Parma, Venezia), relegated (SAL, SAS, FRO), constants
│   ├── models.py                # Dataclasses: Player, PlayerStats, TeamLineup, MatchLineup, MatchFixture, Team, SyncReport
│   ├── pipeline.py              # Ingestion & export coordinator (DataPipeline)
│   ├── players_db.py            # Static evaluation database generator
│   ├── goalkeeper_analyzer.py   # Goalkeeper pairing matrix, attack tiers (1-4), defense ratings
│   ├── fetchers/                # 3-tier HTTP fetchers (Players, Lineups, Fixtures)
│   ├── parsers/                 # RegEx/HTML parsers for players, lineups, fixtures
│   ├── storage/                 # JsonExporter & CsvExporter
│   ├── validators/              # SeasonValidator enforcing 2026/27 invariants
│   └── fallback_data/           # High-fidelity offline JSON datasets
└── tests/
    ├── test_tier1_feature_coverage.py   # 48 tests
    ├── test_tier2_boundary_corner.py    # 15 tests
    ├── test_tier3_combinations.py       # 9 tests
    └── test_tier4_real_world.py         # 7 tests (Total 79 tests in tests/, all passing)
```

---

## 2. Deep Dive: Requirement 1 — Calcolatore Prezzo Massimo (Frontend)

### Current State of `dashboard/index.html`
1. **Tech Stack**:
   - Vanilla JavaScript + Tailwind CSS via CDN (`https://cdn.tailwindcss.com`) + Font Awesome 6.
   - Single-page application with 4 tabs:
     - `portieri`: Recommended goalkeeper combos (cards, estimated costs, difficulty breakdown).
     - `database`: 588 player searchable table with role filters (`ALL`, `P`, `D`, `C`, `A`), QA, FVM, target price, max offer, and buy button.
     - `live-auction`: Roster tracker across 4 roles (3 P, 8 D, 8 C, 6 A) + Rival Budget Tracker for 9 league rivals.
     - `modificatore`: Interactive Defense Modifier calculator based on GK + top 3 DEF average score.
2. **Current Budget & Bid Calculations**:
   - Header summary shows:
     * Crediti Residui: `remainingCredits = totalBudget (500) - userTotalSpent`
     * Slot Rosa: `totalCount / 25`
     * Max Offerta: `remainingSlots > 0 ? (remainingCredits - (remainingSlots - 1)) : remainingCredits`
   - In `renderRivals()`:
     * Rival Max Offerta: `remSlots > 0 ? (r.credits - (remSlots - 1)) : r.credits`
3. **What is Missing**:
   - A dedicated, intelligent **Calcolatore Prezzo Massimo** widget/module that goes beyond simple 1-credit slot reservation:
     * **Rival Max Bid Analysis**: Identifies the opponent with the single highest bidding ceiling $\max_{rival} (C_{rival} - (S_{rival} - 1))$.
     * **Guaranteed Outbid / Winning Price Calculation**: If user max bid > rival max bid, the minimum guaranteed winning bid is $(\text{Top Rival Max Bid} + 1)$.
     * **Safe Budget Allocation (Conservative Ceiling)**: Calculates how much the user can spend on a player without compromising the quality of remaining unfilled slots (e.g. allocating target prices for remaining empty slots).
     * **Target Player Evaluator**: Allows selecting any player from the database (or entering a custom price/role) to evaluate:
       - "Prezzo Consigliato" (based on FVM/Target),
       - "Offerta Massima Sicura" (without starving other roles),
       - "Offerta All-In / Rilancio Massimo" (to beat rivals),
       - "Rischio Overbidding / Verdict".
     * **Interactive UI**: Can be added as a dedicated tab (`tab-calcolatore` / `tab-btn-calcolatore`) and/or embedded directly in the `live-auction` and `database` tabs for rapid auction-time decisions.

---

## 3. Deep Dive: Requirement 2 — Algoritmo "Chi Schiero" / Best Lineup Engine (Backend Python)

### Relevant Data Files & Existing Logic
1. **Probable Lineups Data (`data/probabili_formazioni.json` / `lineups.json`)**:
   - Matchday 1 fixtures (10 matches, 20 teams).
   - Each team provides:
     * `modulo` (e.g., `"3-4-2-1"`, `"4-3-3"`),
     * `titolari` (11 players with `nome`, `ruolo`, `probabilita`, `status`),
     * `panchina` (substitutes with `probabilita`, `status`),
     * `ballottaggi` (contested slots with percentages),
     * `infortunati` (injured players),
     * `squalificati` (suspended players).
2. **Goalkeeper Grid & Defense Ratings (`src/goalkeeper_analyzer.py`)**:
   - `ATTACK_TIER`: Ratings 1 (Top attacco) to 4 (Attacco basso / salvezza).
   - `DEFENSE_RATING`: Team defense strength from 5.5 to 9.5.
   - Match schedule & home/away advantage.
3. **Player Statistics & Target Data (`data/players.json`, `data/players_db.json`)**:
   - `ruolo` (`P`, `D`, `C`, `A`),
   - `fvm_1000`, `qa`, `mv` (media voto), `fm` (fantamedia),
   - `piazzati` (set-piece specialist tags: `RIGORISTA 1°`, `Punizioni`, `Corner`),
   - `mod_rating` (Defense modifier tier: `DIVINO`, `TOP`, `SUPER`, `OTTIMO`, `BUONO`),
   - `xg`, `xa`, `moneyball_index` (from Requirement 3).

### Architecture for `best_lineup.py` & `src/best_lineup.py`
1. **Core Module (`src/best_lineup.py`)**:
   - `LineupOptimizer`:
     * Input: User roster (e.g. 25 players or arbitrary list/dict of players) + Matchday availability.
     * **Strict Invariant Filter**: Filter out any player with `status == "INJURED"`, `status == "SUSPENDED"`, or listed in `infortunati` / `squalificati`, or with `probabilita == 0`.
     * **Player Expected Value Function**:
       $$EV(p) = w_{fm} \cdot FM_p + w_{prob} \cdot (\text{probabilita} / 100) + w_{setpiece} \cdot \text{Bonus}_{p} + w_{moneyball} \cdot MI_{p}$$
     * **Goalkeeper Expected Value Function**:
       $$EV(GK) = MV_{GK} + \text{BonusCleanSheet}(opp\_attack\_tier, is\_home) - \text{ExpectedMalus}(opp\_attack\_tier)$$
     * **Supported Formations**: Classic valid Fantacalcio formations (11 starters, exactly 1 GK):
       `3-4-3`, `3-5-2`, `4-3-3`, `4-4-2`, `4-5-1`, `5-3-2`, `5-4-1`, `3-4-1-2`, `4-2-3-1`.
     * **Defense Modifier Simulator**:
       - When evaluating formations with $\ge 4$ defenders (`4-3-3`, `4-4-2`, `4-5-1`, `5-3-2`, `5-4-1`):
       - Sort starting defenders by expected $MV$ descending, take top 3 + GK.
       - Calculate $\overline{MV} = \frac{MV_{GK} + MV_{D1} + MV_{D2} + MV_{D3}}{4}$.
       - Apply bonus: $\ge 7.25 \to +6$, $\ge 7.00 \to +5$, $\ge 6.75 \to +4$, $\ge 6.50 \to +3$, $\ge 6.25 \to +2$, $\ge 6.00 \to +1$, $< 6.00 \to 0$.
       - Add modifier bonus to total formation expected score.
     * **Bench Formulation**:
       - Formulates 12 substitutes (ordered by role and expected score: 1-2 GK, 3-4 DEF, 3-4 MID, 2-3 ATT).
2. **CLI Executable (`best_lineup.py` or `update_fanta_data.py --lineup`)**:
   - Can run standalone on a JSON roster or sample preset squad and output clear ASCII/table breakdown of the starting XI, bench, formation chosen, defense modifier expected return, and tactical notes.
3. **Acceptance Test Suite (`tests/test_lineup_logic.py`)**:
   - Tests:
     * Valid 11-player formation and exact role counts.
     * Strict exclusion of injured / suspended players.
     * Modifier evaluation when high-rated defenders are available.
     * Deterministic optimal selection for standard squad configurations.

---

## 4. Deep Dive: Requirement 3 — Indice Moneyball (xG, xA, Moneyball Index)

### Player Dataset & Ingestion Model
1. **Existing Dataclasses (`src/models.py`)**:
   - `PlayerStats`: contains `partite_a_voto`, `media_voto`, `fantamedia`, `gol`, `gol_subiti`, `rigori_segnati`, `rigori_sbagliati`, `rigori_parati`, `assist`, `ammonizioni`, `espulsioni`, `clean_sheets`.
   - `Player`: contains `id`, `nome`, `squadra`, `squadra_code`, `ruolo`, `ruolo_mantra`, `qa`, `qi`, `fvm_1000`, `prezzo_target`, `prezzo_max`, `tier`, `piazzati`, `mod_rating`, `mv`, `fm`, `note`, `is_starter`, `stats`, `updated_at`.
2. **Backwards Compatibility Requirements**:
   - Any modification must **not** break existing keys, types, or methods.
   - In `PlayerStats`: add `xg: float = 0.0`, `xa: float = 0.0`.
   - In `Player`: add `xg: float = 0.0`, `xa: float = 0.0`, `moneyball_index: float = 0.0`.
   - In `Player.to_dict()`: keep existing dict schema, adding `xg`, `xa`, `moneyball_index`.
   - In `Player.to_csv_dict()`: keep all 29 original columns, appending `xg`, `xa`, `moneyball_index`.
   - In `players_db.json` (`src/storage/json_exporter.py`): include `xg`, `xa`, `moneyball_index` for each player under `"P"`, `"D"`, `"C"`, `"A"`.
3. **Moneyball Metric Formulation**:
   - Expected Goals ($xG$) and Expected Assists ($xA$) reflect offensive generation independent of luck/finishing variance.
   - Moneyball Index Formula:
     $$xGI = xG + xA$$
     $$\text{Performance Score} = (xG \cdot 3.0) + (xA \cdot 1.5) + (FM \cdot 2.0)$$
     $$\text{Cost Basis} = \max(QA, \text{round}(FVM / 10), 1)$$
     $$\text{Moneyball Index} = \text{round}\left(\frac{\text{Performance Score} \times 10}{\text{Cost Basis}^{0.6}}, 2\right)$$
     (Produces a calibrated score typically between 10.0 and 99.9 highlighting high-performing, lower-cost gems such as Nico Paz, Dorgu, Tavares, Man, Retegui, Gosens, Maldini).
4. **Data Pipeline Integration**:
   - `src/parsers/players_parser.py`: computes / enriches $xG$, $xA$, and $moneyball\_index$ during parsing.
   - `src/fallback_data/fallback_players.json`: update bundled records with realistic $xG$, $xA$, and $moneyball\_index$.
   - `src/pipeline.py` & `src/storage/json_exporter.py`: seamlessly exports enriched datasets to `data/players.json`, `data/players.csv`, `data/players_db.json`.

---

## 5. Summary of Integration Touchpoints

| Requirement | Affected Files | Key Changes | Backwards Compatibility Guarantee |
|---|---|---|---|
| **R1. Prezzo Massimo** | `dashboard/index.html` | Add interactive JS Calculator widget, rival max bid analyzer, safe budget ceiling & target player evaluator. | Preserves all existing tabs, CSS styling, and table actions. |
| **R2. Best Lineup Engine** | `src/best_lineup.py`, `best_lineup.py`, `tests/test_lineup_logic.py` | Create BestLineupEngine supporting formations, modifier bonus, injury/suspension exclusions. | Standalone module + CLI runner, imports clean models. |
| **R3. Moneyball Index** | `src/models.py`, `src/parsers/players_parser.py`, `src/storage/json_exporter.py`, `src/storage/csv_exporter.py`, `src/fallback_data/fallback_players.json` | Add `xg`, `xa`, `moneyball_index` fields with defaults, enrich fallback data & exports. | Strict superset of existing schema: 100% passes all 79 tests. |

---

## 6. Verification Status

- `python3 test_data_integrity.py`: **8 / 8 tests PASS**
- `python3 -m unittest discover tests`: **79 / 79 tests PASS (Tiers 1-4)**
- Python environment: Python 3.9+ standard library only, zero third-party dependencies.
