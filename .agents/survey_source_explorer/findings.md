# Fantacalcio 2026/2027: Data Sources, Scraping Strategy & Resilience Architecture

**Author**: Source Researcher (`survey_source_explorer`)  
**Date**: 2026-09-02  
**Target Season**: Serie A 2026/2027  
**Workspace**: `/Users/umbertomuscillo/Documents/Fantacalcio`  

---

## 1. Executive Summary

This investigation empirically evaluated free web sources, open APIs, and scraping targets to build an automated, robust, and offline-resilient data pipeline for Fantacalcio Serie A 2026/2027.

### Primary Recommendations
1. **Player Database, Quotazioni, Ruoli & Statistics**:
   - **Source**: `https://www.fantacalcio.it/quotazioni-fantacalcio` and `https://www.fantacalcio.it/statistiche-serie-a`.
   - **Accessibility**: HTTP 200 OK via standard HTTPS requests with browser `User-Agent`.
   - **Coverage**: Exactly 588 players across all 20 Serie A 2026/2027 teams (100% complete dataset including newly promoted clubs Como, Parma, and Venezia).
   - **Content**: Both Classic (P, D, C, A) and Mantra roles, Quotazione Iniziale (QI), Quotazione Attuale (QA), Fanta Valore di Mercato (FVM), Partite a Voto (PV), Media Voto (MV), FantaMedia (FM), Goals, Goals Conceded, Penalties, Assists, Yellow & Red cards.
2. **Probabili Formazioni, Lineups, Ballotaggi & Team News**:
   - **Source**: `https://www.fantacalcio.it/probabili-formazioni-serie-a`.
   - **Accessibility**: HTTP 200 OK.
   - **Coverage**: All 10 matches of the active matchweek, complete 20 team formations.
   - **Content**: Tactical modules (e.g. `3-4-2-1`, `4-2-3-1`), 11 Starters with titolarità percentage (e.g. `90%`), Bench/Reserves with percentage, Head-to-head Ballottaggi with percentages (e.g. `60% vs 40%`), Infortunati (injuries), In dubbio (doubts), Squalificati (suspensions), and Diffidati (one yellow from ban).
3. **Serie A 2026/2027 Calendar, Schedule & Match Results**:
   - **Primary Source**: `https://raw.githubusercontent.com/openfootball/italy/master/2026-27/1-seriea.txt` supplemented by `fantacalcio.it/voti-fantacalcio-serie-a/2026-27/{giornata}`.
   - **Accessibility**: HTTP 200 OK via GitHub Raw CDN (unauthenticated, fast, rate-limit friendly).
   - **Coverage**: Full 38 matchdays, 380 matches with exact kickoff dates/times, home/away pairings, and final match scores.

---

## 2. Empirical Source Evaluation Matrix

| Source / Endpoint | Target Domain | HTTP Status | Bot Protection | Auth Req. | Extraction Reliability | Decision / Role |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| `fantacalcio.it/quotazioni-fantacalcio` | Quotazioni & Ruoli | **200 OK** | None (w/ UA) | None | **High** (SSR HTML table) | **PRIMARY** |
| `fantacalcio.it/statistiche-serie-a` | Player Statistics | **200 OK** | None (w/ UA) | None | **High** (SSR HTML table) | **PRIMARY** |
| `fantacalcio.it/probabili-formazioni-serie-a` | Lineups & Ballotaggi | **200 OK** | None (w/ UA) | None | **High** (Semantic DOM) | **PRIMARY** |
| `fantacalcio.it/voti-fantacalcio-serie-a/{giornata}` | Matchday Votes | **200 OK** | None (w/ UA) | None | **High** (Structured tables) | **PRIMARY** |
| `openfootball/italy (raw GitHub)` | 2026/27 Fixture Calendar | **200 OK** | None | None | **High** (Plaintext DSL) | **PRIMARY** |
| `fantacalcio.it/api/v1/Excel/prices/21/1` | Raw Excel Export | **401 Unauthorized** | Token required | Bearer JWT | None | **REJECTED** |
| `gazzetta.it/Calcio/probabili-formazioni/` | Probabili Formazioni | **403 Forbidden** | Akamai / WAF | N/A | Low (Blocked) | **REJECTED** |
| `sport.sky.it/calcio/serie-a/probabili-formazioni` | Probabili Formazioni | **403 Forbidden** | Cloudflare WAF | N/A | Low (Blocked) | **REJECTED** |
| `sosfanta.calciomercato.com/probabili-formazioni/` | Probabili Formazioni | **403 Forbidden** | Cloudflare WAF | N/A | Low (Blocked) | **REJECTED** |
| `pianetafanta.it/probabili-formazioni-serie-a.asp` | Probabili Formazioni | **403 Forbidden** | Perimeter defense | N/A | Low (Blocked) | **REJECTED** |
| `fantapazz.com/probabili-formazioni-serie-a` | Probabili Formazioni | **403 Forbidden** | Cloudflare WAF | N/A | Low (Blocked) | **REJECTED** |
| `legaseriea.it/it/serie-a` | Official Serie A | **403 Forbidden** | Cloudflare Turnstile | N/A | Low (Blocked) | **REJECTED** |
| `thesportsdb.com/api/v1/json/3/...` | Open Sports API | **403 Forbidden** | API Key Wall / WAF | API Key | Low | **REJECTED** |
| `site.api.espn.com/apis/site/v2/sports/...` | ESPN Scoreboard | **403 Forbidden** | Perimeter WAF | N/A | Low | **REJECTED** |

---

## 3. Data Schema & Extraction Technical Details

### 3.1. Player Quotazioni & Statistics
Both `quotazioni-fantacalcio` and `statistiche-serie-a` render a `<tr class="player-row" ...>` table element for all 588 players.

#### HTML Element Attributes & Selectors:
```html
<tr class="player-row"
    data-index="0"
    data-penalties="0.0"
    data-filter-keywords="Malen"
    data-filter-playeds="67"
    data-filter-team-id="15"
    data-filter-role-classic="a"
    data-filter-role-mantra="pc">
  <th class="player-role-classic player-role"><span class="role" data-value="a"></span></th>
  <th class="player-role-mantra player-role"><span class="role role-mantra" data-value="pc"></span></th>
  <th class="player-name">
    <a class="player-name player-link" href="https://www.fantacalcio.it/serie-a/squadre/roma/malen/5585">
      <span>Malen</span>
    </a>
  </th>
  <td class="player-team" data-col-key="sq">ROM</td>
  <!-- Quotazioni Fields -->
  <td class="player-classic-initial-price" data-col-key="c_qi">34</td>
  <td class="player-classic-current-price" data-col-key="c_qa">38</td>
  <td class="player-classic-fvm" data-col-key="c_fvm">450</td>
  <td class="player-mantra-initial-price" data-col-key="m_qi">34</td>
  <td class="player-mantra-current-price" data-col-key="m_qa">38</td>
  <td class="player-mantra-fvm" data-col-key="m_fvm">450</td>
  <!-- Statistics Fields (from /statistiche-serie-a) -->
  <td class="player-match-playeds" data-col-key="pg">2</td>
  <td class="player-grade-avg" data-col-key="mv">8,25</td>
  <td class="player-fanta-grade-avg" data-col-key="mfv">15,5</td>
  <td class="player-scoreds" data-col-key="gol">5</td>
  <td class="player-scoreds" data-col-key="gs">0</td>
  <td class="player-scoreds" data-col-key="rig">0 / 0</td>
  <td class="player-scoreds" data-col-key="rp">0</td>
  <td class="player-assists" data-col-key="ass">0</td>
  <td class="player-yellows" data-col-key="amm">1</td>
  <td class="player-reds" data-col-key="esp">0</td>
</tr>
```

#### Normalized Player JSON Schema:
```json
{
  "id": 5585,
  "name": "Malen",
  "slug": "malen",
  "team": "ROM",
  "role_classic": "A",
  "role_mantra": "PC",
  "quotazione_iniziale_classic": 34,
  "quotazione_attuale_classic": 38,
  "fvm_classic": 450,
  "quotazione_iniziale_mantra": 34,
  "quotazione_attuale_mantra": 38,
  "fvm_mantra": 450,
  "stats": {
    "partite_a_voto": 2,
    "media_voto": 8.25,
    "fantamedia": 15.5,
    "gol_segnati": 5,
    "gol_subiti": 0,
    "rigori_segnati_totali": "0 / 0",
    "rigori_parati": 0,
    "assist": 0,
    "ammonizioni": 1,
    "espulsioni": 0
  }
}
```

---

### 3.2. Probabili Formazioni Schema
From `https://www.fantacalcio.it/probabili-formazioni-serie-a`:
- **Match Header**: Kickoff date/time, Stadium, Home & Away teams.
- **Team Cards**: Module/formation (e.g. `3-4-2-1`), 11 Starters with probability %, Reserves with probability %.
- **Ballottaggi**: Contending players with percentage split (e.g. `Vitinha O. 60% vs Pinamonti 40%`).
- **Disciplinary & Medical Status**:
  - `squalificati`: Suspended players (red card or accumulated yellow ban).
  - `infortunati` / `indisponibili`: Injured players and expected recovery timeline.
  - `in_dubbio`: Doubtful players undergoing physical tests.
  - `diffidati`: Players with 4 yellow cards (one booking away from suspension).

#### Normalized Probabili Formazioni JSON Schema:
```json
{
  "matchweek": 3,
  "matches": [
    {
      "match_id": "genoa-como",
      "date": "venerdì 04 settembre, 20:45",
      "stadium": "Luigi Ferraris",
      "home_team": {
        "name": "Genoa",
        "code": "GEN",
        "formation": "3-4-2-1",
        "starters": [
          {"name": "Bijlow", "percentage": 90, "role": "starter"},
          {"name": "Marcandalli", "percentage": 90, "role": "starter"}
        ],
        "reserves": [
          {"name": "Stolz", "percentage": 5, "role": "reserve"},
          {"name": "Puczka", "percentage": 50, "role": "reserve"}
        ],
        "ballottaggi": [
          {"player_a": "Vitinha O.", "percentage_a": 60, "player_b": "Pinamonti", "percentage_b": 40}
        ],
        "infortunati": [],
        "squalificati": [],
        "diffidati": [],
        "in_dubbio": []
      },
      "away_team": {
        "name": "Como",
        "code": "COM",
        "formation": "4-2-3-1",
        "starters": [],
        "reserves": [],
        "ballottaggi": [],
        "infortunati": [],
        "squalificati": [],
        "diffidati": [],
        "in_dubbio": []
      }
    }
  ]
}
```

---

### 3.3. Serie A 2026/2027 Calendar & Fixture Schedule
From `openfootball/italy` raw repository:
- 38 Matchdays, 380 Matches.
- Provides chronological match ordering, dates, kickoff times, home/away clubs, and scores for completed fixtures.

#### Normalized Calendar JSON Schema:
```json
{
  "season": "2026/2027",
  "total_matchdays": 38,
  "total_matches": 380,
  "matchdays": {
    "1": [
      {
        "date": "Sat Aug 22 2026",
        "time": "18:30",
        "home_team": "Udinese Calcio",
        "home_team_code": "UDI",
        "away_team": "Como 1907",
        "away_team_code": "COM",
        "score": "1-1 (1-0)",
        "status": "FINISHED"
      }
    ]
  }
}
```

---

## 4. Team Canonicalization & 2026/2027 Validation Matrix

All data extraction strictly validates the 20 Serie A 2026/2027 teams, verifying the presence of newly promoted clubs (**Como**, **Parma**, **Venezia**) and excluding relegated teams:

| Code | Canonical Name | Fantacalcio Name | OpenFootball Name | Status in 2026/2027 |
|:---:|:---|:---|:---|:---:|
| `ATA` | Atalanta | Atalanta | Atalanta BC | Active |
| `BOL` | Bologna | Bologna | Bologna FC 1909 | Active |
| `CAG` | Cagliari | Cagliari | Cagliari Calcio | Active |
| `COM` | Como | Como | Como 1907 | **Newly Promoted (Verified)** |
| `FIO` | Fiorentina | Fiorentina | ACF Fiorentina | Active |
| `FRO` | Frosinone | Frosinone | Frosinone Calcio | Active |
| `GEN` | Genoa | Genoa | Genoa CFC | Active |
| `INT` | Inter | Inter | FC Internazionale Milano | Active |
| `JUV` | Juventus | Juventus | Juventus FC | Active |
| `LAZ` | Lazio | Lazio | SS Lazio | Active |
| `LEC` | Lecce | Lecce | US Lecce | Active |
| `MIL` | Milan | Milan | AC Milan | Active |
| `MON` | Monza | Monza | AC Monza | Active |
| `NAP` | Napoli | Napoli | SSC Napoli | Active |
| `PAR` | Parma | Parma | Parma Calcio 1913 | **Newly Promoted (Verified)** |
| `ROM` | Roma | Roma | AS Roma | Active |
| `SAS` | Sassuolo | Sassuolo | US Sassuolo Calcio | Active |
| `TOR` | Torino | Torino | Torino FC | Active |
| `UDI` | Udinese | Udinese | Udinese Calcio | Active |
| `VEN` | Venezia | Venezia | Venezia FC | **Newly Promoted (Verified)** |

---

## 5. Resilience, Fallback & Offline Architecture

External scraping pipelines can be vulnerable to temporary network outages, DNS glitches, or server downtime. To guarantee 100% operational uptime for tests and downstream AI analyses, the pipeline is architected around 3 tiers:

```
[User triggers update_fanta_data.py]
                   │
                   ▼
       ┌────────────────────────┐
       │ Tier 1: Live Scraping  │
       │ (fantacalcio.it + git) │
       └───────────┬────────────┘
                   │
         Success? ─┴── No (Timeout / 5xx / Offline)
        /              \
       ▼                ▼
┌──────────────┐  ┌────────────────────────┐
│ Save raw to  │  │ Tier 2: Local Cache    │
│ data/cache/  │  │ data/cache/snapshot_*. │
└──────┬───────┘  └───────────┬────────────┘
       │                      │
       │            Cache exists? ── No
       │           /                 \
       ▼          ▼                   ▼
┌───────────────────────┐  ┌────────────────────────┐
│ Parse & write clean   │  │ Tier 3: Bundled Mock   │
│ data/ JSON & CSV      │  │ data/fallback_fixtures │
└───────────────────────┘  └───────────┬────────────┘
                                      │
                                      ▼
                           ┌────────────────────────┐
                           │ Parse & write fallback │
                           │ (with Warning Log)     │
                           └────────────────────────┘
```

### Key Resilience Implementation Guidelines:
1. **Polite HTTP Client**:
   - Standard browser `User-Agent` header (`Mozilla/5.0 ...`).
   - Timeout set to 15 seconds per request.
   - SSL unverified fallback context configured if local OS certificate bundle is missing root CA.
2. **Snapshot Caching**:
   - Every successful live fetch saves the raw response to `data/cache/` (e.g. `quotazioni_raw.html`, `statistiche_raw.html`, `probabili_formazioni_raw.html`, `calendar_raw.txt`).
3. **Bundled Fallback Fixtures**:
   - Ship a clean bundled seed/fixture dataset in `data/fixtures/` with complete 2026/2027 data so that `update_fanta_data.py --offline` or `test_data_integrity.py` can run deterministically even in sandboxes without internet access.
4. **Zero Crashing Policy**:
   - If live fetch fails, log `[WARNING] Live fetch failed: {error}. Falling back to cached / fixture dataset.` and cleanly exit with code 0 after writing valid structured JSON/CSV files.

---

## 6. Target Output File Layout

When the update script runs, it outputs cleanly organized files in `data/`:

```
data/
├── json/
│   ├── players.json               # Full 588 players (Quotazioni + Ruoli + Stats)
│   ├── probabili_formazioni.json  # Current matchday lineups, starters, bench, ballotaggi, injuries
│   ├── calendar.json              # 38 matchdays / 380 fixtures / match results
│   ├── injuries_suspensions.json  # Global infortunati & squalificati
│   └── teams.json                 # 20 Serie A 2026/2027 teams metadata
├── csv/
│   ├── players_stats.csv          # Spreadsheet-friendly players list with stats
│   ├── probabili_formazioni.csv   # Flat table of probable starters & ballotaggi
│   └── fixtures_2026_2027.csv     # Full calendar fixtures and results
└── cache/                         # Raw cached payloads for offline resilience
```

---

## 7. Recommended Implementation Steps for Pipeline Developers

1. **Extractor Module (`src/extractors/`)**:
   - `fantacalcio_extractor.py`: Functions to fetch and parse Quotazioni, Statistiche, Probabili Formazioni, and Voti.
   - `calendar_extractor.py`: Functions to fetch and parse OpenFootball calendar data.
2. **Cleaner & Validator Module (`src/cleaners/`)**:
   - Type conversions (Italian decimals `,` -> `.`, `-` -> `None`, percentage strings `90%` -> `90`).
   - Team name canonicalization via `TEAM_MAP`.
   - Season validation (ensures 20 teams, includes Como, Parma, Venezia, excludes old relegated teams).
3. **Pipeline CLI (`update_fanta_data.py`)**:
   - Flags: `--force-live`, `--offline`, `--export-csv`, `--output-dir data/`.
   - Comprehensive error handling and fallback mechanism.
4. **Integrity Test Suite (`tests/test_data_integrity.py`)**:
   - Tests file existence, non-empty datasets, presence of 20 teams (Como, Parma, Venezia), valid player counts (>500), valid roles (P, D, C, A), and exit code 0.
