# Codebase Survey & Target Architecture Report
**Project**: Fantacalcio 2026/2027 Automated Data Pipeline  
**Inspector**: Teamwork Explorer (Codebase Inspector)  
**Date**: 2026-09-02  
**Working Directory**: `/Users/umbertomuscillo/Documents/Fantacalcio`

---

## 1. Executive Summary

This survey provides a comprehensive audit of the `/Users/umbertomuscillo/Documents/Fantacalcio` workspace and delivers an end-to-end modular architecture for the Fantacalcio 2026/2027 automated data pipeline.

### Core Objectives:
1. **Manual Update Pipeline (`update_fanta_data.py`)**: One-command execution to retrieve, clean, validate, and persist players, probable lineups, and Serie A fixtures.
2. **Autonomous Multi-Source Fetching (`src/fetchers/`)**: Scrapers/fetchers for live fantacalcio data with robust retry logic, SSL bypass fallback, and built-in offline fixture fallbacks.
3. **Structured Local Storage (`data/`)**: Production-ready, human-readable and AI-friendly JSON and CSV datasets, maintaining strict backward compatibility with `data/players_db.json` used by `dashboard/index.html`.
4. **Strict Season 2026/2027 Validation (`src/validators/`)**: Programmatic enforcement of the 20 Serie A 2026/2027 teams (guaranteeing inclusion of Como, Parma, and Venezia, and strict exclusion of relegated teams like Sassuolo, Salernitana, and Frosinone).
5. **Automated Verification Suite (`test_data_integrity.py`)**: A thorough acceptance test suite verifying file existence, data schema integrity, team membership, and pipeline execution.

---

## 2. Workspace & Environment Inspection

### 2.1 Directory Structure & Existing Assets
- **Root Directory**:
  - `ORIGINAL_REQUEST.md`: System prompt & project specification.
  - `dashboard/`: Contains `index.html` (39KB), a rich TailwindCSS-based war room and live auction dashboard. Crucially, line 441 of `index.html` fetches `../data/players_db.json` structured as `{"P": [...], "D": [...], "C": [...], "A": [...]}`.
  - `data/`: Contains WhatsApp backup media files (53 media files: audio `.opus`, photos `.jpg`, stickers `.webp`, and league rules `.pdf`) along with `data/players_db.json` (195KB, 588 player records).
  - `src/`: Contains legacy scripts:
    1. `build_official_database.py`: Regex parser that extracts 588 players from a hardcoded internal markdown path (`HTML_PATH = '/Users/umbertomuscillo/.gemini/antigravity/brain/.../content.md'`).
    2. `goalkeeper_analyzer.py`: Analytical model for goalkeeper pairings and match difficulty tiers.
    3. `players_db.py`: Static dictionary of ~70 top players with manual stats (prezzo_target, MV, FM, notes).
  - `.agents/`: Agent collaboration workspaces (`orchestrator_1/`, `sentinel_1/`, `survey_codebase_explorer/`).

### 2.2 Python Runtime Environment
- **Interpreter**: `/usr/bin/python3` (macOS system Python 3.9.6).
- **Installed Packages**: Minimal system distribution (`altgraph`, `future`, `macholib`, `six`, `wheel`, `pip 21.2.4`). Third-party libraries like `requests` or `beautifulsoup4` are **not** installed in system python.
- **Network & SSL Finding**: Default macOS Python SSL certificates can encounter verification issues when accessing certain HTTPS endpoints. A custom SSL context using `ssl.create_default_context()` with fallback to unverified SSL context is necessary to guarantee 100% network connectivity.
- **Architectural Decision (Zero External Dependencies)**:
  The pipeline must be constructed using **pure Python standard library** (`urllib.request`, `html.parser`, `re`, `json`, `csv`, `pathlib`, `logging`, `argparse`, `unittest`, `dataclasses`). This ensures **zero friction**, instant execution on any macOS/Linux environment, and no virtualenv dependency.

### 2.3 Critical Defects & Gaps in Current Codebase
1. **Missing Pipeline Entry Point**: `update_fanta_data.py` does not exist.
2. **Missing Test Suite**: `test_data_integrity.py` does not exist.
3. **Hardcoded Ephemeral Paths**: `src/build_official_database.py` relies on a deleted/temporary session file path in `~/.gemini/antigravity/brain/...`.
4. **Season 2026/2027 Team Inconsistency in Legacy Code**:
   In `src/build_official_database.py`, `TEAM_NAMES` incorrectly included relegated teams (`Frosinone` and `Sassuolo`) while missing `Empoli` and `Verona`.
   - Relegated teams (to exclude): `Salernitana`, `Sassuolo`, `Frosinone`.
   - Promoted teams (to include): `Parma`, `Como`, `Venezia`.
   - The correct 20 teams are: Atalanta, Bologna, Cagliari, Como, Empoli, Fiorentina, Genoa, Inter, Juventus, Lazio, Lecce, Milan, Monza, Napoli, Parma, Roma, Torino, Udinese, Venezia, Verona.
5. **Lack of Automated Fetchers & Parsers**: No modular scrapers exist for live probable lineups (`probabili_formazioni`), Serie A calendar (`calendario`), or dynamic player statistics updates.

---

## 3. Proposed Modular Architecture

### 3.1 Architecture Overview

```
/Users/umbertomuscillo/Documents/Fantacalcio/
├── update_fanta_data.py              # CLI Entry Point: Orchestrates entire data refresh
├── test_data_integrity.py            # Test Suite: Automated acceptance & integrity checks
├── src/
│   ├── __init__.py                   # Package initializer
│   ├── config.py                     # Constants, 2026/27 team mappings, file paths, URLs
│   ├── pipeline.py                   # DataPipeline orchestrator (Fetch -> Parse -> Validate -> Export)
│   ├── fetchers/                     # Autonomous web data retrieval
│   │   ├── __init__.py
│   │   ├── base_fetcher.py           # HTTP client (urllib, User-Agents, retries, SSL context)
│   │   ├── players_fetcher.py        # Scrapes/fetches players listone & live market values
│   │   ├── lineups_fetcher.py        # Scrapes/fetches probable lineups & ballots
│   │   └── fixtures_fetcher.py       # Scrapes/fetches Serie A 2026/27 schedule & results
│   ├── parsers/                      # Data parsing, cleaning & normalization
│   │   ├── __init__.py
│   │   ├── players_parser.py         # Normalizes roles (Classic/Mantra), prices (500 budget), tiers, notes
│   │   ├── lineups_parser.py         # Extracts starters (11), bench, percentages, unavailable players
│   │   └── fixtures_parser.py        # Normalizes match days, home/away pairings, match statuses
│   ├── storage/                      # Persistence & dual-format exporters
│   │   ├── __init__.py
│   │   ├── json_exporter.py          # Exports JSON (both flat & role-grouped for dashboard)
│   │   └── csv_exporter.py           # Exports tabular CSV files for Excel/AI processing
│   ├── validators/                   # Season 2026/2027 & data integrity rules
│   │   ├── __init__.py
│   │   └── season_validator.py       # Enforces 20 Serie A teams, promotes/relegates check, sanity rules
│   └── goalkeeper_analyzer.py        # Goalkeeper pairing matrix generator (retained & modernized)
└── data/
    ├── players_db.json               # Legacy & Dashboard compatible JSON (grouped by P, D, C, A)
    ├── players.json                  # Normalized list of all Serie A players (JSON)
    ├── players.csv                   # Tabular player database (CSV)
    ├── probabili_formazioni.json     # Probable lineups by match/team (JSON)
    ├── probabili_formazioni.csv      # Tabular lineups & ballot percentages (CSV)
    ├── calendario_serie_a.json       # Serie A 2026/27 complete 38-round fixtures (JSON)
    ├── calendario_serie_a.csv        # Tabular fixtures dataset (CSV)
    └── sync_report.json              # Execution metadata & data audit log
```

---

## 4. Module Specifications

### 4.1 `src/config.py`
Centralized configuration repository:
- **Paths**: Absolute paths to `data/` directory and all output files.
- **Season 2026/2027 Team Definitions**:
  - `SERIE_A_TEAMS_2026_2027`: Set of exactly 20 valid team names:
    `{"Atalanta", "Bologna", "Cagliari", "Como", "Empoli", "Fiorentina", "Genoa", "Inter", "Juventus", "Lazio", "Lecce", "Milan", "Monza", "Napoli", "Parma", "Roma", "Torino", "Udinese", "Venezia", "Verona"}`.
  - `PROMOTED_TEAMS`: `{"Como", "Parma", "Venezia"}`.
  - `RELEGATED_TEAMS`: `{"Salernitana", "Sassuolo", "Frosinone"}`.
  - `TEAM_CODE_MAP`: 3-letter abbreviation mappings (e.g. `ATA` -> `Atalanta`, `COM` -> `Como`, `PAR` -> `Parma`, `VEN` -> `Venezia`, `EMP` -> `Empoli`, `VER` -> `Verona`).
- **Auction Parameters**: Default budget 500 crediti, scaled target prices (`prezzo_target = max(1, round(fvm_1000 / 2))`, `prezzo_max = max(1, round(prezzo_target * 1.25))`).
- **Network Configuration**: Custom User-Agents, request timeout (10s), max retries (3), SSL context configuration.

### 4.2 `src/fetchers/` (Autonomous Data Ingestion)
- **`base_fetcher.py`**:
  - Abstract base class with robust HTTP fetching via `urllib.request`.
  - Configures realistic browser User-Agent headers, timeout handling, and SSL certificate fallback context.
  - Implements exponential backoff retry logic.
- **`players_fetcher.py`**:
  - Autonomous web fetcher targeting public fantacalcio feeds / listoni (e.g. Fantacalcio.it / PianetaFanta / SOS Fanta public endpoints/pages).
  - Includes an embedded high-fidelity fallback dataset containing the complete listone of 588+ Serie A 2026/2027 players across all 20 teams, guaranteeing 100% uptime even during offline execution or network disruptions.
- **`lineups_fetcher.py`**:
  - Fetches probable lineups for the upcoming Serie A matchday (Formazione titolare 11 vs 11, modulo, ballottaggi, indisponibili/squalificati).
- **`fixtures_fetcher.py`**:
  - Fetches the complete 38-round Serie A 2026/2027 calendar and match pairings.

### 4.3 `src/parsers/` (Data Cleaning & Normalization)
- **`players_parser.py`**:
  - Normalizes player names, roles (`P`, `D`, `C`, `A`), Mantra roles (`por`, `dc;dd`, `m;c`, `w;a`, `pc`, etc.).
  - Calculates scaled auction metrics (`prezzo_target`, `prezzo_max` on 500 credit base).
  - Tags penalty takers (`piazzati`), defense modifier ratings (`mod_rating`: `DIVINO`, `TOP`, `SUPER`, `OTTIMO`, `BUONO`), and strategic auction tiers (`tier`).
- **`lineups_parser.py`**:
  - Structures lineups into standardized schema with exactly 11 starters per team, ballot percentages, and injury reports.
- **`fixtures_parser.py`**:
  - Normalizes match schedules, rounds (Giornata 1 - 38), home/away indicators, and calculates goalkeeper pairing difficulty ratings.

### 4.4 `src/storage/` (Dual-Format Exporters)
- **`json_exporter.py`**:
  - Writes `data/players_db.json` (role-grouped dictionary `{"P": [...], "D": [...], "C": [...], "A": [...]}`) to maintain seamless backward compatibility with `dashboard/index.html`.
  - Writes flat lists `data/players.json`, `data/probabili_formazioni.json`, `data/calendario_serie_a.json`, and `data/sync_report.json`.
- **`csv_exporter.py`**:
  - Writes UTF-8 encoded, comma-separated files: `data/players.csv`, `data/probabili_formazioni.csv`, `data/calendario_serie_a.csv`.

### 4.5 `src/validators/` (Data Integrity & Season Compliance)
- **`season_validator.py`**:
  - Verifies that all 20 Serie A 2026/2027 teams are present.
  - Verifies presence of promoted teams: Como, Parma, Venezia.
  - Strictly asserts **absence** of relegated teams: Salernitana, Sassuolo, Frosinone.
  - Verifies data integrity: valid roles (`P`, `D`, `C`, `A`), non-negative prices, minimum player thresholds (>= 400 total, >= 40 P, >= 120 D, >= 120 C, >= 80 A).
  - Returns a detailed validation report with passed/failed checks.

### 4.6 `update_fanta_data.py` (CLI Entry Point)
- Provides standard CLI with flags:
  ```bash
  python3 update_fanta_data.py [--all] [--players] [--lineups] [--fixtures] [--force] [--verbose]
  ```
- Workflow:
  1. Initializes logging and loads `src/config.py`.
  2. Runs fetchers to retrieve players, lineups, and fixtures.
  3. Parses and enriches datasets.
  4. Runs `SeasonValidator` against extracted data.
  5. Exports to `data/` in both JSON and CSV formats.
  6. Saves `data/sync_report.json` and logs a formatted summary table.
  7. Exits with returncode 0 on success (or non-zero with error trace on failure).

### 4.7 `test_data_integrity.py` (Automated Test Suite)
Implements 8 programmatic test cases using Python's `unittest`:
1. `test_pipeline_execution`: Runs `update_fanta_data.py` via subprocess, asserts exit code 0.
2. `test_generated_files_exist`: Asserts existence and non-emptiness of all 7 target files in `data/`.
3. `test_teams_2026_2027_membership`: Asserts all 20 Serie A teams exist; asserts Como, Parma, Venezia exist; asserts Sassuolo, Salernitana, Frosinone are absent.
4. `test_players_schema_and_types`: Verifies all required fields (`nome`, `squadra`, `ruolo`, `qa`, `fvm_1000`, `prezzo_target`) are properly typed.
5. `test_player_counts_sanity`: Verifies player count distribution (total >= 400, P >= 40, D >= 120, C >= 120, A >= 80).
6. `test_lineups_data_integrity`: Verifies all 10 fixtures for the matchday have 11 starters per team and valid team names.
7. `test_fixtures_data_integrity`: Verifies 38 matchdays exist with valid pairings.
8. `test_json_and_csv_consistency`: Asserts row count and content parity between JSON and CSV exports.

---

## 5. Target Data Schema Specifications

### 5.1 Players Dataset (`data/players.json` & `data/players.csv`)
| Field | Type | Description | Example |
|---|---|---|---|
| `id` | Integer | Unique identifier | `101` |
| `nome` | String | Player full/display name | `"Lautaro Martinez"` |
| `squadra` | String | Serie A team name | `"Inter"` |
| `squadra_code` | String | 3-letter team code | `"INT"` |
| `ruolo` | String | Classic role (`P`, `D`, `C`, `A`) | `"A"` |
| `ruolo_mantra` | String | Mantra roles | `"pc"` |
| `qa` | Integer | Quotazione Attuale (current price) | `38` |
| `fvm_1000` | Integer | FantaValore di Mercato (base 1000) | `340` |
| `prezzo_target` | Integer | Recommended target bid (base 500) | `170` |
| `prezzo_max` | Integer | Maximum ceiling bid (base 500) | `190` |
| `tier` | String | Tactical auction tier | `"1 Top Assoluto"` |
| `piazzati` | String | Set pieces / penalty duty | `"RIGORISTA 2°, Capitano"` |
| `mod_rating` | String | Defense modifier rating | `""` |
| `mv` | Float | Average rating (Media Voto) | `6.60` |
| `fm` | Float | Fantamedia | `8.80` |
| `note` | String | Tactical & auction notes | `"Capocannoniere e trascinatore dell'Inter"` |
| `is_starter` | Boolean | Likely regular starter | `true` |

### 5.2 Probable Lineups (`data/probabili_formazioni.json` & `data/probabili_formazioni.csv`)
| Field | Type | Description | Example |
|---|---|---|---|
| `match_id` | String | Match identifier | `"2026_G01_INT_GEN"` |
| `giornata` | Integer | Matchday number (1 - 38) | `1` |
| `home_team` | String | Home club name | `"Inter"` |
| `away_team` | String | Away club name | `"Genoa"` |
| `home_formation` | String | Home tactical module | `"3-5-2"` |
| `away_formation` | String | Away tactical module | `"3-5-2"` |
| `home_titolarissimi` | List[String] | 11 starting players | `["Sommer", "Pavard", "Acerbi", ...]` |
| `home_ballottaggi` | Dict/String | Ballots with % chance | `{"Darmian": 60, "Dumfries": 40}` |
| `home_indisponibili` | List[String] | Injured/suspended players | `["Buchanan"]` |
| `away_titolarissimi` | List[String] | 11 starting players | `["Gollini", "Vogliacco", "Bani", ...]` |
| `away_ballottaggi` | Dict/String | Ballots with % chance | `{"Vitinha": 55, "Ekuban": 45}` |
| `away_indisponibili` | List[String] | Injured/suspended players | `["Matturro"]` |
| `last_updated` | String | ISO UTC timestamp | `"2026-09-02T14:30:00Z"` |

### 5.3 Serie A Fixtures (`data/calendario_serie_a.json` & `data/calendario_serie_a.csv`)
| Field | Type | Description | Example |
|---|---|---|---|
| `match_id` | String | Unique fixture ID | `"G01_INT_GEN"` |
| `giornata` | Integer | Round number (1 - 38) | `1` |
| `home_team` | String | Home team | `"Inter"` |
| `away_team` | String | Away team | `"Genoa"` |
| `home_score` | Optional[Int] | Goals scored by home team | `null` |
| `away_score` | Optional[Int] | Goals scored by away team | `null` |
| `status` | String | Match status | `"scheduled"` |
| `difficolta_portieri` | Dict | Match difficulty rating (1: Easy, 2: Med, 3: Hard) | `{"Inter": 1, "Genoa": 3}` |

---

## 6. Implementation Strategy for the Team

To execute the project efficiently and cleanly:

1. **Step 1: Configuration & Base Infrastructure**
   - Create `src/config.py` with 2026/2027 team sets, team code dictionaries, file paths, and default configurations.
   - Implement `src/fetchers/base_fetcher.py` with standard library `urllib` and SSL fallbacks.
2. **Step 2: Fetchers & Parsers**
   - Implement `src/fetchers/players_fetcher.py`, `src/fetchers/lineups_fetcher.py`, `src/fetchers/fixtures_fetcher.py`.
   - Implement `src/parsers/players_parser.py`, `src/parsers/lineups_parser.py`, `src/parsers/fixtures_parser.py`.
3. **Step 3: Storage Exporters & Validators**
   - Implement `src/storage/json_exporter.py` and `src/storage/csv_exporter.py`.
   - Implement `src/validators/season_validator.py`.
   - Implement `src/pipeline.py` orchestrator.
4. **Step 4: CLI & Test Suite**
   - Implement `update_fanta_data.py`.
   - Implement `test_data_integrity.py`.
5. **Step 5: Execution & Verification**
   - Execute `python3 update_fanta_data.py` to generate clean `data/` files.
   - Execute `python3 test_data_integrity.py` to verify acceptance criteria.
   - Verify `dashboard/index.html` loads smoothly against generated data.

---

## 7. Conclusion
The proposed architecture fully addresses all requirements (R1, R2, R3, R4) and acceptance criteria of `ORIGINAL_REQUEST.md`. It eliminates previous defects (such as ephemeral paths and outdated team lists), guarantees zero external dependency friction on macOS Python 3.9+, and equips the Fantacalcio project with a professional data pipeline and automated verification framework.
