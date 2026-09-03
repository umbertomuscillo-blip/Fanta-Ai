# Project: Fantacalcio 2026/2027 Automated Data Pipeline

## Architecture
The Fantacalcio 2026/2027 Data Pipeline is an automated, modular, zero-external-dependency Python system that retrieves, cleans, structures, validates, and exports complete Serie A 2026/2027 fantasy football data.

### Architectural Principles
1. **Zero External Dependencies**: Built entirely using Python 3.9+ standard library (`urllib.request`, `ssl`, `json`, `csv`, `re`, `html.parser`, `dataclasses`, `pathlib`, `logging`, `unittest`). Runs directly on macOS / Linux out-of-the-box.
2. **3-Tier Resilient Ingestion**:
   - Tier 1: Live HTTP requests with realistic headers to verified endpoints (`fantacalcio.it`, `openfootball`).
   - Tier 2: Local cache snapshots for fast re-runs and transient network issues.
   - Tier 3: High-fidelity bundled offline dataset guaranteeing 100% test reproducibility and zero CI failures.
3. **Dual Storage Format + Backward Compatibility**:
   - Flat JSON & CSV files in `data/` for AI consumption and data science pipelines (`players.json`, `players.csv`, `probabili_formazioni.json`, `probabili_formazioni.csv`, `calendario_serie_a.json`, `calendario_serie_a.csv`, `teams.json`, `teams.csv`).
   - Backward-compatible `data/players_db.json` structured by role (`P`, `D`, `C`, `A`) to preserve full functionality of `dashboard/index.html`.
4. **Strict Serie A 2026/2027 Invariant Validation**:
   - Enforces the presence of all 20 active Serie A 2026/2027 clubs including newly promoted: Como (`COM`), Parma (`PAR`), Venezia (`VEN`).
   - Strictly verifies exclusion of relegated clubs (e.g. Salernitana, Sassuolo, Frosinone).
   - Enforces schema validity, player counts (>500), valid roles (`P`, `D`, `C`, `A`), positive prices, starting 11 per lineup, and 380 total calendar fixtures.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Configuration & Serie A 2026/2027 Domain Model | Constants, team mappings (20 clubs incl. Como, Parma, Venezia), paths, URLs | M1 | Survey |
| 2 | Resilient Web Fetchers & HTTP Client | Multi-tier HTTP client with SSL handling, User-Agent headers, cache & offline fallback | M2 | Survey |
| 3 | Player & Statistics Parser | HTML/Data parser extracting 588+ players, classic/mantra roles, quotazioni, stats | M2 | Survey |
| 4 | Probable Lineups Parser | Parser extracting matchday, 10 fixtures, starting XI, bench, ballotaggi %, injuries | M2 | Survey |
| 5 | Season Calendar & Results Parser | 38 matchdays, 380 matches for Serie A 2026/2027 | M2 | Survey |
| 6 | Storage Exporter Layer | JSON & CSV serializers for players, lineups, fixtures, teams + `players_db.json` | M3 | Survey |
| 7 | Season & Data Validator | Validates 2026/2027 team roster, excludes relegated, verifies invariant rules | M3 | Survey |
| 8 | Pipeline Orchestrator & CLI Runner | `update_fanta_data.py` and `src/pipeline.py` executing full sync and reporting | M3 | Survey |
| 9 | Programmatic Test Suite | `test_data_integrity.py` verifying files, teams, exit codes, data invariants | E2E | Survey |
| 10 | Comprehensive E2E Testing (Tiers 1-4) | Category-Partition, BVA, Pairwise Combinations, Real-World Workloads | E2E | Survey |
| 11 | Adversarial Hardening (Tier 5) | White-box edge cases, malformed data, network dropouts, schema drift | Final | Survey |
| 12 | Agent-as-Judge Coherence Review | Independent reviewer evaluation on fantasy soccer domain realism | Final | Survey |
| 13 | Forensic Integrity Verification | Auditor zero-tolerance check against hardcoding, facades, or cheating | Final | Survey |

---

## Code Layout
- `update_fanta_data.py`: Main CLI executable entry point (`--all`, `--players`, `--lineups`, `--fixtures`, `--verbose`)
- `test_data_integrity.py`: Automated programmatic acceptance test suite (checks file existence, 2026/27 teams, schema invariants)
- `src/`
  - `__init__.py`
  - `config.py`: Serie A 2026/2027 team constants, paths, source URLs
  - `models.py`: Dataclasses for Player, Lineup, Fixture, Team, SyncReport
  - `fetchers/`
    - `__init__.py`
    - `base_fetcher.py`: Base HTTP request handler, SSL context, cache & fallback logic
    - `players_fetcher.py`: Ingests player listone and stats from fantacalcio.it
    - `lineups_fetcher.py`: Ingests probabili formazioni from fantacalcio.it
    - `fixtures_fetcher.py`: Ingests 38-giornata Serie A calendar from openfootball
  - `parsers/`
    - `__init__.py`
    - `players_parser.py`: Extracts players, roles, quotazioni, stats
    - `lineups_parser.py`: Extracts matchday, formations, starters, bench, ballotaggi
    - `fixtures_parser.py`: Extracts 380 match schedule
  - `storage/`
    - `__init__.py`
    - `json_exporter.py`: Writes `data/players.json`, `data/probabili_formazioni.json`, `data/calendario_serie_a.json`, `data/teams.json`, `data/players_db.json`, `data/sync_report.json`
    - `csv_exporter.py`: Writes `data/players.csv`, `data/probabili_formazioni.csv`, `data/calendario_serie_a.csv`, `data/teams.csv`
  - `validators/`
    - `__init__.py`
    - `season_validator.py`: Enforces 2026/2027 team roster, excludes relegated, validates invariants
  - `pipeline.py`: Coordinates fetch -> parse -> validate -> export -> sync_report
- `data/`: Local storage directory for output datasets (JSON, CSV) and fallback cache

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Domain & Configuration | `src/config.py`, `src/models.py`, team registries & dataclasses | none | DONE |
| M2 | Data Ingestion & Parsers | `src/fetchers/`, `src/parsers/`, bundled fallback datasets | M1 | DONE |
| M3 | Storage, Validation & CLI Runner | `src/storage/`, `src/validators/`, `src/pipeline.py`, `update_fanta_data.py` | M2 | DONE |
| E2E | E2E Testing Track | Test infra, `test_data_integrity.py`, Tiers 1-4 test cases -> `TEST_READY.md` | M1 | DONE |
| Final | Final Acceptance & Hardening | Pass 100% E2E tests, Tier 5 Adversarial Hardening, Agent-as-Judge review, Forensic Audit | M3, E2E | DONE |

---

## Interface Contracts

### `src/config.py`
- `SERIE_A_TEAMS_2026_2027`: `dict[str, str]` mapping 20 3-letter codes to full team names:
  `{'ATA': 'Atalanta', 'BOL': 'Bologna', 'CAG': 'Cagliari', 'COM': 'Como', 'EMP': 'Empoli', 'FIO': 'Fiorentina', 'GEN': 'Genoa', 'INT': 'Inter', 'JUV': 'Juventus', 'LAZ': 'Lazio', 'LEC': 'Lecce', 'MIL': 'Milan', 'MON': 'Monza', 'NAP': 'Napoli', 'PAR': 'Parma', 'ROM': 'Roma', 'TOR': 'Torino', 'UDI': 'Udinese', 'VEN': 'Venezia', 'VER': 'Verona'}`
- `PROMOTED_TEAMS_2026_2027`: `{'COM': 'Como', 'PAR': 'Parma', 'VEN': 'Venezia'}`
- `RELEGATED_TEAMS`: `{'SAL': 'Salernitana', 'SAS': 'Sassuolo', 'FRO': 'Frosinone'}`
- `DATA_DIR`: `Path` to project `data/`

### `src/models.py`
- `Player`: `id: int, nome: str, squadra: str, ruolo: str, ruolo_mantra: list[str], quotazione_iniziale: int, quotazione_attuale: int, fvm: int, prezzo_target: int, stats: dict`
- `TeamLineup`: `squadra: str, modulo: str, titolari: list[dict], panchina: list[dict], ballottaggi: list[dict], infortunati: list[str], squalificati: list[str]`
- `MatchLineup`: `giornata: int, casa: TeamLineup, trasferta: TeamLineup`
- `MatchFixture`: `giornata: int, data_ora: str, squadra_casa: str, squadra_trasferta: str, gol_casa: Optional[int], gol_trasferta: Optional[int], status: str`
- `SyncReport`: `timestamp: str, success: bool, players_count: int, lineups_count: int, fixtures_count: int, teams_count: int, execution_time_sec: float, errors: list[str]`

### `src/pipeline.py`
- `run_pipeline(fetch_players=True, fetch_lineups=True, fetch_fixtures=True, force_fallback=False, verbose=False) -> SyncReport`: Executes complete pipeline and exports JSON/CSV files to `data/`.

### `update_fanta_data.py`
- CLI flags: `--all`, `--players`, `--lineups`, `--fixtures`, `--offline-fallback`, `--verbose`. Exits `0` on success.

### `test_data_integrity.py`
- Invocation: `python3 test_data_integrity.py`
- Verifies:
  1. Existence of all required output files (`players.json`, `players.csv`, `probabili_formazioni.json`, `probabili_formazioni.csv`, `calendario_serie_a.json`, `calendario_serie_a.csv`, `teams.json`, `teams.csv`, `players_db.json`, `sync_report.json`).
  2. Exactly 20 Serie A 2026/2027 teams present; Como, Parma, Venezia present; Salernitana, Sassuolo, Frosinone absent.
  3. Players dataset >500 records, all roles `P`, `D`, `C`, `A` present, valid quotazioni.
  4. Lineups dataset contains 10 matches / 20 teams, each with exactly 11 starters.
  5. Calendar dataset contains 38 giornate and 380 total matches.
  6. Exit code is 0.
