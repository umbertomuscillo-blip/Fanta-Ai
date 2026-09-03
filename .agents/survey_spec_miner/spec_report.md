# Specification Report — Fantacalcio 2026/2027 Automated Data Pipeline

**Document Version:** 1.0.0  
**Status:** Authoritative Specification  
**Project:** Fantacalcio 2026/2027 Automated Data Pipeline  
**Workspace:** `/Users/umbertomuscillo/Documents/Fantacalcio`  
**Target Execution Command:** `python update_fanta_data.py`  
**Verification Command:** `python test_data_integrity.py`  
**Author:** Spec Miner Agent  

---

## 1. Executive Summary & Scope

The Fantacalcio 2026/2027 automated data pipeline is a local, self-contained data ingestion, cleaning, normalization, and persistence system. Triggered on demand via `python update_fanta_data.py`, it scrapes, transforms, validates, and stores up-to-date Serie A and Fantacalcio data into `data/` in standardized JSON and CSV formats.

The pipeline serves as the authoritative local source of truth for:
1. **Official Player Database & Statistics** (Classic roles `P/D/C/A`, Mantra roles, Quotazioni `QA`/`QI`, FVM /1000, 500-budget targets, penalties/set-pieces, modifier ratings).
2. **Probable Lineups & Matchday Insights** (10 matches per matchday, starters, benches, percentage duels/ballottaggi, injured, suspended).
3. **Official Season Calendar & Fixtures** (Full 38 matchdays, 380 matches, home/away, timestamps, statuses, difficulty ratings).
4. **Serie A 2026/2027 Teams Metadata** (20 official clubs including promoted teams Como, Parma, Venezia; excluding relegated teams Salernitana, Sassuolo, Frosinone).
5. **Backwards Compatibility** with existing `dashboard/index.html` and AI analysis tools.

---

## 2. Authoritative Serie A 2026/2027 Team Specification

### 2.1 The 20 Official Serie A 2026/2027 Clubs

| # | Club Name (Canonical) | 3-Letter Code | Promoted Status | City | Stadium | Primary Color |
|---|---|---|---|---|---|---|
| 1 | **Atalanta** | `ATA` | Retained | Bergamo | Gewiss Stadium | Blue / Black |
| 2 | **Bologna** | `BOL` | Retained | Bologna | Renato Dall'Ara | Red / Blue |
| 3 | **Cagliari** | `CAG` | Retained | Cagliari | Unipol Domus | Red / Blue |
| 4 | **Como** | `COM` | **Promoted (2026/27)** | Como | Giuseppe Sinigaglia | Royal Blue |
| 5 | **Empoli** | `EMP` | Retained | Empoli | Carlo Castellani | Blue |
| 6 | **Fiorentina** | `FIO` | Retained | Firenze | Artemio Franchi | Purple |
| 7 | **Genoa** | `GEN` | Retained | Genova | Luigi Ferraris | Red / Blue |
| 8 | **Inter** | `INT` | Retained | Milano | Giuseppe Meazza (San Siro) | Black / Blue |
| 9 | **Juventus** | `JUV` | Retained | Torino | Allianz Stadium | Black / White |
| 10 | **Lazio** | `LAZ` | Retained | Roma | Stadio Olimpico | Sky Blue / White |
| 11 | **Lecce** | `LEC` | Retained | Lecce | Stadio Via del Mare | Yellow / Red |
| 12 | **Milan** | `MIL` | Retained | Milano | Giuseppe Meazza (San Siro) | Red / Black |
| 13 | **Monza** | `MON` | Retained | Monza | U-Power Stadium | Red / White |
| 14 | **Napoli** | `NAP` | Retained | Napoli | Diego Armando Maradona | Sky Blue |
| 15 | **Parma** | `PAR` | **Promoted (2026/27)** | Parma | Ennio Tardini | Yellow / Blue |
| 16 | **Roma** | `ROM` | Retained | Roma | Stadio Olimpico | Yellow / Red |
| 17 | **Torino** | `TOR` | Retained | Torino | Stadio Olimpico Grande Torino | Maroon (Granata) |
| 18 | **Udinese** | `UDI` | Retained | Udine | Bluenergy Stadium | Black / White |
| 19 | **Venezia** | `VEN` | **Promoted (2026/27)** | Venezia | Pier Luigi Penzo | Orange / Black / Green |
| 20 | **Verona** | `VER` | Retained | Verona | Marcantonio Bentegodi | Yellow / Blue |

### 2.2 Explicit Relegation Constraints (Must NOT Appear in 2026/2027 Active Roster)
The following clubs were relegated from Serie A and **must be excluded** from all 2026/2027 active Serie A lists, lineups, and calendars:
- ❌ **Salernitana** (`SAL`)
- ❌ **Sassuolo** (`SAS`)
- ❌ **Frosinone** (`FRO`)

### 2.3 Team Name Normalization Map (Aliases -> Canonical Name)
To prevent scraping fragmentation across different media sources (e.g. Gazzetta, Sky Sport, Fantacalcio.it, Flashscore), all team strings must be normalized via:

```python
TEAM_NORMALIZATION_MAP = {
    # Atalanta
    "atalanta": "Atalanta", "ata": "Atalanta", "atalanta bc": "Atalanta",
    # Bologna
    "bologna": "Bologna", "bol": "Bologna", "bologna fc": "Bologna",
    # Cagliari
    "cagliari": "Cagliari", "cag": "Cagliari", "cagliari calcio": "Cagliari",
    # Como
    "como": "Como", "com": "Como", "como 1907": "Como",
    # Empoli
    "empoli": "Empoli", "emp": "Empoli", "empoli fc": "Empoli",
    # Fiorentina
    "fiorentina": "Fiorentina", "fio": "Fiorentina", "acf fiorentina": "Fiorentina",
    # Genoa
    "genoa": "Genoa", "gen": "Genoa", "genoa cfc": "Genoa",
    # Inter
    "inter": "Inter", "int": "Inter", "internazionale": "Inter", "inter milan": "Inter", "fc internazionale": "Inter",
    # Juventus
    "juventus": "Juventus", "juv": "Juventus", "juve": "Juventus", "juventus fc": "Juventus",
    # Lazio
    "lazio": "Lazio", "laz": "Lazio", "ss lazio": "Lazio",
    # Lecce
    "lecce": "Lecce", "lec": "Lecce", "us lecce": "Lecce",
    # Milan
    "milan": "Milan", "mil": "Milan", "ac milan": "Milan",
    # Monza
    "monza": "Monza", "mon": "Monza", "ac monza": "Monza",
    # Napoli
    "napoli": "Napoli", "nap": "Napoli", "ssc napoli": "Napoli",
    # Parma
    "parma": "Parma", "par": "Parma", "parma calcio": "Parma", "parma calcio 1913": "Parma",
    # Roma
    "roma": "Roma", "rom": "Roma", "as roma": "Roma",
    # Torino
    "torino": "Torino", "tor": "Torino", "torino fc": "Torino", "toro": "Torino",
    # Udinese
    "udinese": "Udinese", "udi": "Udinese", "udinese calcio": "Udinese",
    # Venezia
    "venezia": "Venezia", "ven": "Venezia", "venezia fc": "Venezia",
    # Verona
    "verona": "Verona", "ver": "Verona", "hellas verona": "Verona", "hellas": "Verona", "hellas verona fc": "Verona"
}
```

---

## 3. Data Schemas & Data Contracts

All data resides in the `data/` directory. For every entity type, both a **structured JSON** (for rich nested data / AI context) and a **flattened CSV** (for rapid tabular processing / human inspection) are produced.

### 3.1 Entity 1: Teams (`data/teams.json` and `data/teams.csv`)

#### JSON Schema (`data/teams.json`)
```json
[
  {
    "id": "INT",
    "code": "INT",
    "name": "Inter",
    "full_name": "FC Internazionale Milano",
    "city": "Milano",
    "stadium": "Giuseppe Meazza (San Siro)",
    "coach": "Simone Inzaghi",
    "promoted": false,
    "primary_color": "#000000",
    "secondary_color": "#00529F"
  }
]
```

#### CSV Schema (`data/teams.csv`)
- **Headers:** `id,code,name,full_name,city,stadium,coach,promoted,primary_color,secondary_color`
- **Types:** `str,str,str,str,str,str,str,bool,str,str`

---

### 3.2 Entity 2: Players (`data/players.json`, `data/players.csv`, and `data/players_db.json`)

#### 3.2.1 Primary JSON Schema (`data/players.json`)
A flat array of all active Serie A 2026/2027 players (~550-650 total):
```json
[
  {
    "id": "5421",
    "nome": "Lautaro Martinez",
    "squadra": "Inter",
    "squadra_code": "INT",
    "ruolo": "A",
    "ruoli_mantra": ["Pc"],
    "qa": 38,
    "qi": 36,
    "fvm_1000": 170,
    "prezzo_target": 85,
    "prezzo_max": 95,
    "tier": "1 Top Assoluto (1° Slot)",
    "stats": {
      "presenze": 28,
      "media_voto": 6.60,
      "fantamedia": 8.80,
      "gol": 22,
      "gol_subiti": 0,
      "rigori_segnati": 4,
      "rigori_sbagliati": 1,
      "rigori_parati": 0,
      "assist": 5,
      "ammonizioni": 3,
      "espulsioni": 0,
      "clean_sheets": 0
    },
    "tattica": {
      "titolare_probabile": true,
      "piazzati": "2° Rigorista, Capitano",
      "is_rigorista": true,
      "is_punizioni": false,
      "is_corner": false,
      "mod_rating": "",
      "note": "Capocannoniere e trascinatore dell'Inter. 20-25 gol attesi."
    },
    "updated_at": "2026-09-02T14:30:00Z"
  }
]
```

#### 3.2.2 Flat CSV Schema (`data/players.csv`)
- **Headers:**
  `id,nome,squadra,squadra_code,ruolo,ruoli_mantra,qa,qi,fvm_1000,prezzo_target,prezzo_max,tier,presenze,media_voto,fantamedia,gol,gol_subiti,rigori_segnati,rigori_sbagliati,rigori_parati,assist,ammonizioni,espulsioni,clean_sheets,titolare_probabile,piazzati,mod_rating,note,updated_at`
- **Field Constraints:**
  - `ruolo` ∈ `{"P", "D", "C", "A"}`
  - `ruoli_mantra`: Semicolon-delimited (e.g. `Dd;Ds;E` or `Por` or `M;C` or `Pc`)
  - `qa`: integer >= 1
  - `fvm_1000`: integer >= 1 (standard Fantacalcio.it scale on 1000 credits)
  - `prezzo_target`: integer >= 1 (calibrated to 500-credit league budget)
  - `prezzo_max`: integer >= `prezzo_target`

#### 3.2.3 Compatibility Grouped JSON (`data/players_db.json`)
Maintained for backwards compatibility with `dashboard/index.html` and existing tools:
```json
{
  "P": [ { "nome": "Svilar", "squadra": "Roma", "ruolo": "P", ... } ],
  "D": [ { "nome": "Dimarco", "squadra": "Inter", "ruolo": "D", ... } ],
  "C": [ { "nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", ... } ],
  "A": [ { "nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", ... } ]
}
```

---

### 3.3 Entity 3: Probable Lineups (`data/lineups.json` and `data/lineups.csv`)

#### 3.3.1 JSON Schema (`data/lineups.json`)
Contains probable lineups for the current/upcoming matchday (10 matches):
```json
{
  "matchday": 1,
  "season": "2026/2027",
  "updated_at": "2026-09-02T14:30:00Z",
  "matches": [
    {
      "match_id": "2026_G01_INT_LEC",
      "home_team": "Inter",
      "home_team_code": "INT",
      "away_team": "Lecce",
      "away_team_code": "LEC",
      "match_datetime": "2026-08-23T20:45:00Z",
      "home_lineup": {
        "modulo": "3-5-2",
        "titolari": [
          { "nome": "Sommer", "ruolo": "P", "probabilita": 90, "numero_maglia": 1 },
          { "nome": "Pavard", "ruolo": "D", "probabilita": 80, "numero_maglia": 28 },
          { "nome": "Acerbi", "ruolo": "D", "probabilita": 75, "numero_maglia": 15 },
          { "nome": "Bastoni", "ruolo": "D", "probabilita": 90, "numero_maglia": 95 },
          { "nome": "Dumfries", "ruolo": "D", "probabilita": 60, "numero_maglia": 2 },
          { "nome": "Barella", "ruolo": "C", "probabilita": 90, "numero_maglia": 23 },
          { "nome": "Calhanoglu", "ruolo": "C", "probabilita": 95, "numero_maglia": 20 },
          { "nome": "Mkhitaryan", "ruolo": "C", "probabilita": 80, "numero_maglia": 22 },
          { "nome": "Dimarco", "ruolo": "D", "probabilita": 90, "numero_maglia": 32 },
          { "nome": "Thuram", "ruolo": "A", "probabilita": 85, "numero_maglia": 9 },
          { "nome": "Martinez L.", "ruolo": "A", "probabilita": 95, "numero_maglia": 10 }
        ],
        "panchina": [
          { "nome": "Martinez Jo.", "ruolo": "P" },
          { "nome": "Darmian", "ruolo": "D" },
          { "nome": "Bisseck", "ruolo": "D" },
          { "nome": "Carlos Augusto", "ruolo": "D" },
          { "nome": "Frattesi", "ruolo": "C" },
          { "nome": "Zielinski", "ruolo": "C" },
          { "nome": "Asllani", "ruolo": "C" },
          { "nome": "Taremi", "ruolo": "A" },
          { "nome": "Arnautovic", "ruolo": "A" }
        ],
        "ballottaggi": [
          {
            "ruolo": "D",
            "titolare": "Dumfries",
            "sfidante": "Darmian",
            "percentuale_titolare": 60,
            "percentuale_sfidante": 40
          },
          {
            "ruolo": "D",
            "titolare": "Acerbi",
            "sfidante": "De Vrij",
            "percentuale_titolare": 55,
            "percentuale_sfidante": 45
          }
        ],
        "infortunati": [
          {
            "nome": "Buchanan",
            "ruolo": "D",
            "motivo": "Frattura tibia",
            "rientro_previsto": "Ottobre 2026"
          }
        ],
        "squalificati": []
      },
      "away_lineup": {
        "modulo": "4-2-3-1",
        "titolari": [ ... ],
        "panchina": [ ... ],
        "ballottaggi": [ ... ],
        "infortunati": [ ... ],
        "squalificati": [ ... ]
      }
    }
  ]
}
```

#### 3.3.2 Flat CSV Schema (`data/lineups.csv`)
- **Headers:**
  `matchday,match_id,team,team_code,is_home,opponent,opponent_code,player_name,ruolo,status,probability,duel_opponent,duel_split,injury_note,suspension_note`
- **Field Constraints:**
  - `status` ∈ `{"STARTER", "BENCH", "INJURED", "SUSPENDED"}`
  - `is_home`: boolean (`True`/`False`)
  - Exactly 11 `STARTER` records per team per match (with exactly 1 `P` starter).

---

### 3.4 Entity 4: Calendar & Fixtures (`data/calendar.json` and `data/calendar.csv`)

#### 3.4.1 JSON Schema (`data/calendar.json`)
Contains all 38 matchdays and 380 matches of the Serie A 2026/2027 season:
```json
[
  {
    "matchday": 1,
    "match_id": "2026_G01_INT_LEC",
    "home_team": "Inter",
    "home_team_code": "INT",
    "away_team": "Lecce",
    "away_team_code": "LEC",
    "match_datetime": "2026-08-23T20:45:00Z",
    "status": "FINISHED",
    "home_score": 2,
    "away_score": 0,
    "difficulty_home": 1,
    "difficulty_away": 3,
    "season": "2026/2027"
  }
]
```

#### 3.4.2 Flat CSV Schema (`data/calendar.csv`)
- **Headers:**
  `matchday,match_id,home_team,home_team_code,away_team,away_team_code,match_datetime,status,home_score,away_score,difficulty_home,difficulty_away,season`
- **Field Constraints:**
  - `matchday`: integer 1 to 38
  - Total records: exactly 380
  - `status` ∈ `{"SCHEDULED", "LIVE", "FINISHED", "POSTPONED"}`
  - `difficulty_home`, `difficulty_away`: integer ∈ `{1, 2, 3}` (1 = Facile, 2 = Media, 3 = Difficile)

---

## 4. File Layout Specification

The pipeline outputs exclusively into `data/` and is executable from project root:

```
/Users/umbertomuscillo/Documents/Fantacalcio/
├── update_fanta_data.py          # Main manual update script (Entry point)
├── test_data_integrity.py        # Automated test suite (Verification entry point)
├── data/
│   ├── teams.json                # 20 Serie A 2026/27 clubs metadata
│   ├── teams.csv                 # 20 Serie A clubs tabular
│   ├── players.json              # Full players array with stats, ratings, set-pieces
│   ├── players.csv               # Tabular players list
│   ├── players_db.json           # Grouped by role (P, D, C, A) for dashboard compatibility
│   ├── lineups.json              # Probable lineups (10 matches, starters, duels, injuries)
│   ├── lineups.csv               # Tabular probable lineups
│   ├── calendar.json             # 38 matchdays / 380 matches season calendar
│   └── calendar.csv              # Tabular season calendar
├── src/
│   ├── scrapers/                 # Web scrapers / collectors for Fantacalcio, Lineups, Calendar
│   ├── models/                   # Pydantic / Dataclass models for data validation
│   ├── processors/               # Data cleaning, team normalization, target pricing logic
│   └── exporters/                # JSON and CSV export serializers
└── dashboard/
    └── index.html                # Interactive War Room visual dashboard
```

---

## 5. Programmatic Verification Rules (`test_data_integrity.py`)

The automated integrity verification suite must enforce the following strict assertions:

```python
"""
Suite: test_data_integrity.py
Acceptance Test Rules for Fantacalcio 2026/2027 Data Pipeline
"""

# Rule 1: All 9 Output Files Exist and are Non-Empty
EXPECTED_FILES = [
    "data/teams.json",
    "data/teams.csv",
    "data/players.json",
    "data/players.csv",
    "data/players_db.json",
    "data/lineups.json",
    "data/lineups.csv",
    "data/calendar.json",
    "data/calendar.csv"
]

# Rule 2: Exact 20 Serie A 2026/2027 Teams
REQUIRED_TEAMS = {
    "Atalanta", "Bologna", "Cagliari", "Como", "Empoli",
    "Fiorentina", "Genoa", "Inter", "Juventus", "Lazio",
    "Lecce", "Milan", "Monza", "Napoli", "Parma",
    "Roma", "Torino", "Udinese", "Venezia", "Verona"
}
PROMOTED_TEAMS = {"Como", "Parma", "Venezia"}
FORBIDDEN_TEAMS = {"Salernitana", "Sassuolo", "Frosinone"}

# Rule 3: Player Constraints
# - Total players >= 500
# - Roles must be strictly within {'P', 'D', 'C', 'A'}
# - All 4 roles populated (P >= 50, D >= 150, C >= 150, A >= 100)
# - QA >= 1, FVM >= 1, Prezzo_Target >= 1
# - No player assigned to a forbidden/relegated team

# Rule 4: Lineup Constraints
# - Contains 10 matches (20 distinct teams) for the matchday
# - Exactly 11 starters per team
# - Exactly 1 'P' starter per team
# - Ballottaggi split percentages sum to 100% per duel
# - Starters do not overlap with injured or suspended players

# Rule 5: Calendar Constraints
# - Exactly 380 matches across 38 matchdays (10 per matchday)
# - Each team plays exactly 38 games (19 home, 19 away)
# - Every pair of teams plays exactly 2 head-to-head matches (1 home, 1 away)
# - home_team != away_team in every match

# Rule 6: Process Return Code
# - python update_fanta_data.py exits with code 0
```

---

## 6. Agent-as-Judge Evaluation Rubric

An independent reviewer agent assesses the pipeline output against 5 core criteria on a **Pass / Fail** (or 1-5 scale) basis:

| Criteria # | Evaluation Area | Target Standard | Failure Condition |
|---|---|---|---|
| **C1** | **Season 2026/27 Strictness** | Exactly 20 teams; Como, Parma, Venezia present; Salernitana, Sassuolo, Frosinone absent. | Any relegated club found in active Serie A list or missing promoted club. |
| **C2** | **Role & Pricing Realism** | Roles correspond to real Serie A listone; top stars (Lautaro, Vlahovic, Calhanoglu, Dimarco, Svilar) have realistic top tiers; prices reflect 500-credit budget. | Goalkeepers listed as Strikers, Lautaro valued at 1 credit, or FVM scale anomalies. |
| **C3** | **Lineup Tactical Logic** | Formations are authentic (3-5-2, 4-3-3, etc.); 1 GK + 10 outfield players; realistic starters, sensible ballottaggi (e.g. 50/50, 60/40). | 2 GKs in starters, < 11 starters, non-existent players in lineups. |
| **C4** | **Calendar Completeness** | Exactly 38 matchdays, 380 games, perfectly symmetric home/away fixture matrix. | Missing matchdays, mismatched teams, or < 380 total fixtures. |
| **C5** | **Data Format & Interoperability** | Clean JSON and CSV syntax; UTF-8 encoding preserving accents (e.g. Çalhanoğlu/Calhanoglu, Soulé, Dybala, Raspadori); valid schema parsing in Python/JS. | JSON parse errors, unescaped CSV commas/quotes, corrupted characters (`Ã¨`, `â‚¬`). |

---

## 7. Discovered Features & Edge Cases

### 7.1 Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|---|---|---|---|---|---|---|
| 1 | **CLI Pipeline** | `update_fanta_data.py` Runner | Master manual trigger script that runs all sub-scrapers and exporters. | CLI args (`--category`, `--force`, `--quiet`) | Exit code `0`, updated `data/` files | Non-zero exit code, logged traceback | `ORIGINAL_REQUEST.md` (R1) |
| 2 | **Team Validation** | 2026/27 Serie A Team Enforcer | Validates team membership against the 20 official clubs (promoted included, relegated rejected). | Team string / raw data | Normalized canonical team name & code | Raises `InvalidTeamError` / drops invalid records | `ORIGINAL_REQUEST.md` (R4), `src/goalkeeper_analyzer.py` |
| 3 | **Player Ingestion** | Player Scraper & Normalizer | Scrapes player roster, roles (Classic/Mantra), QA, FVM, stats, and set pieces. | Web sources / listone HTML | `data/players.json`, `data/players.csv` | Logs warning, fallback to cached base DB | `src/build_official_database.py`, `src/players_db.py` |
| 4 | **Target Pricing** | 500-Credit Target Scaler | Scales official 1000-point FVM to a 500-point league budget with tiering. | `fvm_1000` (int) | `prezzo_target` (int), `prezzo_max` (int), `tier` (str) | Defaults to min 1 credit if FVM is invalid | `src/build_official_database.py` |
| 5 | **Lineup Scraper** | Probable Lineups Extractor | Extracts matchday probable formations, 11 starters, bench, duels/ballotaggi, and injury reports. | Matchday index / web source | `data/lineups.json`, `data/lineups.csv` | Graceful fallback to previous matchday lineup | `ORIGINAL_REQUEST.md` (R2) |
| 6 | **Calendar Generator** | 380-Match Fixtures Generator | Parses or generates full 38-matchday Serie A schedule with home/away difficulty tiers. | 20 Serie A clubs | `data/calendar.json`, `data/calendar.csv` | Enforces 380 games invariant | `src/goalkeeper_analyzer.py` |
| 7 | **Dashboard Compatibility**| `players_db.json` Exporter | Exports players grouped by role dictionary (`{"P": [], "D": [], "C": [], "A": []}`) for UI. | Unified players list | `data/players_db.json` | Re-constructs empty role buckets | `dashboard/index.html` (line 440) |
| 8 | **Set-Piece Detection** | Piazzati & Penalty Taker Annotator | Identifies 1st/2nd penalty takers, direct free-kick and corner specialists. | Player name & notes | `piazzati`, `is_rigorista`, `is_punizioni` tags | Empty string if unassigned | `src/build_official_database.py` (PENALTY_TAKERS) |
| 9 | **Modifier Classifier** | Defense Modifier Rater | Categorizes defenders with modifier potential (`DIVINO`, `SUPER`, `TOP`, `OTTIMO`, `BUONO`). | Player name & average rating | `mod_rating` tag | None/empty string if standard defender | `src/build_official_database.py` (MOD_DEFENDERS) |
| 10 | **Integrity Test** | `test_data_integrity.py` Suite | Automated test suite verifying file existence, team set, player counts, lineups, and calendar invariants. | `data/` directory contents | `pytest` / test runner exit code 0 or 1 | Fails with clear diagnostic assertion message | `ORIGINAL_REQUEST.md` (Programmatic Verification) |

### 7.2 Edge Cases & Observed Behavior

| # | Feature | Input / Edge Case | Observed / Required Behavior |
|---|---|---|---|
| 1 | **Team Normalization** | Input team name is `"Hellas Verona"` or `"AC Milan"` or `"Internazionale"`. | Normalizes to `"Verona"`, `"Milan"`, `"Inter"` with canonical codes `VER`, `MIL`, `INT`. |
| 2 | **Relegated Club Encountered** | Scraper encounters players from `"Sassuolo"`, `"Salernitana"`, or `"Frosinone"` from cached old list. | Filter out / exclude from active Serie A dataset or flag as transferred/inactive. |
| 3 | **Promoted Club Parsing** | Players belonging to `"Como"`, `"Parma"`, or `"Venezia"`. | Correctly parsed and attributed to valid Serie A 2026/27 clubs with full stats and lineups. |
| 4 | **Accent & Special Characters** | Turkish/European names (e.g., `Çalhanoğlu`, `Laurienté`, `Nico Paz`, `Kvaratskhelia`). | Preserved cleanly in UTF-8 without Unicode corruption or mojibake. |
| 5 | **Dual / Slash Lineup Starters** | Lineup displays `"Dumfries / Darmian"` in starter slot. | Assign primary starter (highest probability, e.g. Dumfries 60%) to `titolari` and record duel in `ballottaggi`. |
| 6 | **Zero-Minute / New Transfers** | Newly signed players with 0 appearances, 0 goals, no historical votes. | Set `presenze: 0`, `media_voto: 0.0`, `fantamedia: 0.0`, but assign valid `qa` and `fvm_1000`. |
| 7 | **Network Failure during Scrape** | Target web source is unreachable (HTTP 500/timeout/rate limit). | Pipeline must catch network exception, log error, and fallback to local cached baseline without crashing. |
| 8 | **Budget Boundary in Target Scaler** | Minimum FVM = 1 (scaled /2 gives 0.5). | Ensure `prezzo_target = max(1, round(fvm / 2))` so every player costs at least 1 credit. |
| 9 | **Multiple Mantra Roles** | Multi-role player (e.g. `Dd;Ds;E` or `M;C` or `W;T;A`). | Parsed as string list in JSON `["Dd", "Ds", "E"]` and semicolon-separated in CSV `"Dd;Ds;E"`. |
| 10 | **Empty Injuried / Suspended List** | Team has no injured or suspended players. | Outputs empty list `[]` in JSON and empty string `""` in CSV rather than `null`/`NaN`. |

---

## 8. Summary & Next Steps

This specification defines the complete data contract for the Fantacalcio 2026/2027 automated pipeline. All downstream tracks (Architecture `PROJECT.md`, Implementation Track `src/` & `update_fanta_data.py`, and E2E Testing Track `test_data_integrity.py`) must conform strictly to the schemas and invariants documented herein.
