# Data Architecture, Pipeline & Schemas Analysis Report
**Fantacalcio 2026/2027: Baseline Pipeline & Advanced Features (R1, R2, R3)**

---

## 1. Executive Summary

This report delivers a thorough inspection of the existing Fantacalcio 2026/2027 codebase, data files in `data/`, scraping/ingestion pipelines (`update_fanta_data.py`, `src/`), and formal specifications for the upcoming advanced features requested in `ORIGINAL_REQUEST.md`:
1. **R1: Calcolatore Prezzo Massimo (Frontend / Live Auction)** — JS-driven max bid and rival tracking algorithm for `dashboard/index.html`.
2. **R2: Algoritmo "Chi Schiero" (Backend Python `best_lineup.py`)** — Mathematical starting XI and bench optimizer crossing user rosters with `lineups.json`, `statistics.json`/`players.json`, goalkeeper grid, and defense modifier rules.
3. **R3: Indice Moneyball (Backend Python & Pipeline Integration)** — Expected Goals (`xG`), Expected Assists (`xA`), and Moneyball Index enrichment of player datasets to surface undervalued fantasy assets.

---

## 2. Existing Data Inventory & Schema Specifications

The project maintains dual JSON/CSV representations in `data/` along with backward-compatible role-grouped structures.

### 2.1 Players Dataset (`data/players.json`, `data/players.csv`, `data/players_db.json`)

#### `data/players.json` (Flat List of 588+ Players)
```json
[
  {
    "id": 5585,
    "nome": "Malen",
    "squadra": "Roma",
    "squadra_code": "ROM",
    "ruolo": "A",
    "ruolo_mantra": "pc",
    "qa": 38,
    "qi": 34,
    "fvm_1000": 450,
    "prezzo_target": 225,
    "prezzo_max": 281,
    "tier": "1 Top Assoluto (1° Slot)",
    "piazzati": "1° Rigorista / Perno Attacco Roma",
    "mod_rating": "",
    "mv": 8.25,
    "fm": 15.5,
    "note": "",
    "is_starter": true,
    "stats": {
      "partite_a_voto": 2,
      "media_voto": 8.25,
      "fantamedia": 15.5,
      "gol": 5,
      "gol_subiti": 0,
      "rigori_segnati": 0,
      "rigori_sbagliati": 0,
      "rigori_parati": 0,
      "assist": 0,
      "ammonizioni": 1,
      "espulsioni": 0,
      "clean_sheets": 0
    },
    "updated_at": "2026-09-02T12:52:10Z"
  }
]
```

#### Field Definitions
| Field | Type | Description |
|---|---|---|
| `id` | integer | Unique player ID from Fantacalcio.it |
| `nome` | string | Player display name |
| `squadra` | string | Full canonical club name (e.g. "Como", "Parma", "Inter") |
| `squadra_code` | string | 3-letter canonical club code (e.g. `COM`, `PAR`, `INT`) |
| `ruolo` | string (`"P"`, `"D"`, `"C"`, `"A"`) | Classic fantasy soccer role |
| `ruolo_mantra` | string | Semicolon-separated Mantra roles (e.g. `"por"`, `"dd;e"`, `"pc"`) |
| `qa` | integer | Current quotation / Quotazione Attuale |
| `qi` | integer | Initial quotation / Quotazione Iniziale |
| `fvm_1000` | integer | Fantavalore di Mercato on a 1000-credit base |
| `prezzo_target` | integer | Recommended target bid scaled to a 500-credit budget |
| `prezzo_max` | integer | Maximum ceiling bid recommendation |
| `tier` | string | Classification (e.g. "1 Top Assoluto", "2 Semi-Top", "Crack Assoluto") |
| `piazzati` | string | Set piece designations (e.g. "1° Rigorista", "Punizioni", "Corner") |
| `mod_rating` | string | Defense modifier grade (`"TOP"`, `"DIVINO"`, `"SUPER"`, `"OTTIMO"`, `"BUONO"`) |
| `mv` | float | Historical Media Voto |
| `fm` | float | Historical Fantamedia |
| `note` | string | Tactical commentary and fantasy advice |
| `is_starter` | boolean | Probable starter status |
| `stats` | object (`PlayerStats`) | Object containing 12 statistical counters |
| `updated_at` | string (ISO-8601) | Timestamp of last sync |

#### `data/players_db.json` (Role-Grouped Structure)
Used directly by `dashboard/index.html` for instant client-side filtering without heavy runtime transformations:
```json
{
  "P": [ { "nome": "Sommer", "squadra": "Inter", "ruolo": "P", ... } ],
  "D": [ { "nome": "Dimarco", "squadra": "Inter", "ruolo": "D", ... } ],
  "C": [ { "nome": "Calhanoglu", "squadra": "Inter", "ruolo": "C", ... } ],
  "A": [ { "nome": "Lautaro Martinez", "squadra": "Inter", "ruolo": "A", ... } ]
}
```

---

### 2.2 Probable Lineups Dataset (`data/lineups.json`, `data/probabili_formazioni.json`)

Contains the 10 Serie A matchday fixtures with 20 starting teams (11 starters each):
```json
{
  "giornata": 1,
  "season": "2026/2027",
  "matches": [
    {
      "match_id": "2026_G01_UDI_COM",
      "giornata": 1,
      "date_str": "2026-08-22T18:30:00Z",
      "stadium": "Stadio Serie A",
      "home_team": "Udinese",
      "home_team_code": "UDI",
      "away_team": "Como",
      "away_team_code": "COM",
      "home_lineup": {
        "squadra": "Udinese",
        "squadra_code": "UDI",
        "modulo": "3-4-2-1",
        "titolari": [
          { "nome": "Okoye", "ruolo": "P", "probabilita": 90, "status": "STARTER" },
          { "nome": "Abankwah", "ruolo": "D", "probabilita": 80, "status": "STARTER" }
        ],
        "panchina": [
          { "nome": "Padelli", "ruolo": "P", "probabilita": 1, "status": "BENCH" }
        ],
        "ballottaggi": [
          {
            "ruolo": "D",
            "titolare": "Kamara H.",
            "sfidante": "Zemura",
            "percentuale_titolare": 60,
            "percentuale_sfidante": 40
          }
        ],
        "infortunati": [
          { "nome": "Sanchez", "motivo": "Lesione muscolare", "rientro": "Ottobre 2026" }
        ],
        "squalificati": []
      },
      "away_lineup": {
        "squadra": "Como",
        "squadra_code": "COM",
        "modulo": "4-2-3-1",
        "titolari": [ ... 11 items ... ],
        "panchina": [ ... ],
        "ballottaggi": [ ... ],
        "infortunati": [ ... ],
        "squalificati": [ ... ]
      }
    }
  ]
}
```

---

### 2.3 Calendar & Goalkeeper Matrix Dataset (`data/calendar.json`, `data/calendario_serie_a.json`)

Covers the full 38-matchday / 380-match schedule with integrated goalkeeper difficulty ratings (1 = Easy, 2 = Medium, 3 = Hard):
```json
[
  {
    "match_id": "2026_G01_UDI_COM",
    "giornata": 1,
    "date_str": "Sat Aug 22 2026 18:30",
    "home_team": "Udinese",
    "home_team_code": "UDI",
    "away_team": "Como",
    "away_team_code": "COM",
    "home_score": 1,
    "away_score": 1,
    "status": "FINISHED",
    "difficolta_portieri": {
      "Udinese": 1,
      "Como": 1
    },
    "season": "2026/2027"
  }
]
```

---

### 2.4 Teams Dataset (`data/teams.json`, `data/teams.csv`)

Tracks all 20 Serie A 2026/2027 clubs including promoted sides (Como, Parma, Venezia):
```json
[
  {
    "id": "COM",
    "code": "COM",
    "name": "Como",
    "full_name": "Como 1907",
    "city": "Como",
    "stadium": "Giuseppe Sinigaglia",
    "coach": "Cesc Fabregas",
    "promoted": true,
    "primary_color": "#003399",
    "secondary_color": "#FFFFFF"
  }
]
```

---

## 3. Pipeline Ingestion & Scraping Architecture

The pipeline in `update_fanta_data.py` and `src/` implements a zero-external-dependency, 3-tier resilient architecture:

```
[ CLI: update_fanta_data.py ]
             │
             ▼
    [ src/pipeline.py ]
    ┌───────────────────────────┬───────────────────────────┬───────────────────────────┐
    │ 1. Players Fetch & Parse  │ 2. Lineups Fetch & Parse  │ 3. Fixtures Fetch & Parse │
    │    (PlayersFetcher/Parser)│    (LineupsFetcher/Parser)│   (FixturesFetcher/Parser)│
    └─────────────┬─────────────┴─────────────┬─────────────┴─────────────┬─────────────┘
                  │                           │                           │
                  └───────────────────────────┼───────────────────────────┘
                                              ▼
                                   [ src/validators/ ]
                                  (SeasonValidator: 2026/27
                                   20 Clubs, Roles, Invariants)
                                              │
                                              ▼
                                   [ src/storage/ ]
                                  (JsonExporter & CsvExporter)
                                              │
                                              ▼
                                 data/*.json, data/*.csv
```

### 3-Tier Fallback Mechanism
1. **Tier 1 (Live HTTP)**: Fetches live SSR HTML from `fantacalcio.it` (quotazioni, statistiche, probabili formazioni) and fixtures from `openfootball`.
2. **Tier 2 (Local Cache)**: Reads raw cached responses from `data/cache/` if network fails.
3. **Tier 3 (Bundled High-Fidelity Dataset)**: Loads fallback datasets from `src/fallback_data/` to guarantee deterministic tests and 100% test reproducibility in offline environments.

---

## 4. Formulations & Specifications for R1, R2, R3

### 4.1 R1: Calcolatore Prezzo Massimo (Frontend Dashboard Widget)

#### Mathematical Rules
1. **User Max Bid**:
   $$\text{MaxBid}_{\text{user}} = \max\left(1, \text{Budget}_{\text{remaining}} - (\text{Slots}_{\text{remaining}} - 1)\right)$$
2. **Role-Specific Max Bid**:
   $$\text{MaxBid}_{\text{role}} = \max\left(1, \text{Budget}_{\text{remaining}} - (\text{Slots}_{\text{total\_rem}} - 1) - \sum_{r \neq \text{role}} \text{MinCostRemaining}(r)\right)$$
   where minimum cost per remaining slot is 1 credit.
3. **Rival Ceiling Tracker**:
   $$\text{MaxBid}_{\text{rival}_i} = \max\left(1, \text{Credits}_i - (\text{SlotsRemaining}_i - 1)\right)$$
4. **Winning Target Recommendation**:
   $$\text{RecommendedBid}(\text{player}) = \min\left(\text{MaxBid}_{\text{user}}, \max_i(\text{MaxBid}_{\text{rival}_i}) + 1\right)$$

#### Frontend Widget State Schema
```typescript
interface LiveAuctionState {
  userBudget: number;              // Initial 500
  userSpent: number;
  userRoster: {
    P: Array<{ name: string; price: number }>;  // Limit: 3
    D: Array<{ name: string; price: number }>;  // Limit: 8
    C: Array<{ name: string; price: number }>;  // Limit: 8
    A: Array<{ name: string; price: number }>;  // Limit: 6
  };
  rivals: Array<{
    id: string;
    name: string;
    credits: number;
    slotsAcquired: number;         // Out of 25
    maxBid: number;
  }>;
}
```

---

### 4.2 R2: Algoritmo "Chi Schiero" (Backend Python `best_lineup.py`)

#### Problem Boundary
Given a user roster input (JSON file or CLI dict of up to 25 players), cross-reference with `data/lineups.json`, `data/players.json`, `data/calendar.json`, and the goalkeeper difficulty grid to output:
1. Optimal tactical formation: one of `3-4-3`, `3-5-2`, `4-3-3`, `4-4-2`, `4-5-1`, `5-3-2`, `5-4-1`.
2. Starting XI (1 Goalkeeper, $D$ Defenders, $C$ Midfielders, $A$ Attackers).
3. Bench ordering (Goalkeeper reserve, Defenders, Midfielders, Attackers in priority order).
4. Defense modifier analysis (if $D \ge 4$).
5. Safety filter: Zero starters who are `INJURED`, `SQUALIFICATI`, or have 0% playing probability.

#### Rating and Optimization Metric
For each outfield player $p$:
$$\text{ExpectedScore}(p) = P_{\text{start}}(p) \cdot \left[ \text{FM}(p) + \Delta_{\text{home/away}} + \Delta_{\text{opp\_difficulty}} + \Delta_{\text{penalties}} \right]$$
where:
- $P_{\text{start}}(p) \in [0.0, 1.0]$ is extracted from `probabili_formazioni.json` titolari % (or ballotaggio %).
- $\text{FM}(p)$ is Fantamedia (default 6.0 if no historical data).
- $\Delta_{\text{home/away}} = +0.25$ if playing at home, $-0.10$ if playing away against top team.
- $\Delta_{\text{opp\_difficulty}} = +0.50$ (vs Easy/Difficulty 1), $0.0$ (vs Medium/2), $-0.60$ (vs Hard/3).
- $\Delta_{\text{penalties}} = +0.75$ if primary penalty taker (`piazzati` contains `"1° Rigorista"`).

For Goalkeeper $g$:
$$\text{ExpectedGK}(g) = P_{\text{start}}(g) \cdot \left[ \text{FM}(g) + \text{Bonus}_{\text{clean\_sheet\_prob}} - \text{ExpectedGoalsConceded}(g) \right]$$

For Defense Modifier ($D \ge 4$):
$$\text{ModBonus} = \begin{cases}
+6 & \text{if } \text{Avg}_{\text{GK+Top3Def}} \ge 7.25 \\
+5 & \text{if } 7.00 \le \text{Avg} < 7.25 \\
+4 & \text{if } 6.75 \le \text{Avg} < 7.00 \\
+3 & \text{if } 6.50 \le \text{Avg} < 6.75 \\
+2 & \text{if } 6.25 \le \text{Avg} < 6.50 \\
+1 & \text{if } 6.00 \le \text{Avg} < 6.25 \\
0 & \text{otherwise}
\end{cases}$$

#### Output Schema (`best_lineup.json` / CLI Output)
```json
{
  "giornata": 1,
  "modulo_scelto": "3-4-3",
  "expected_total_score": 76.45,
  "modificatore_applicato": false,
  "modificatore_expected_bonus": 0,
  "titolari": [
    {
      "id": 101,
      "nome": "Sommer",
      "ruolo": "P",
      "squadra": "Inter",
      "avversario": "Monza (C)",
      "probabilita_titolare": 95,
      "expected_score": 6.20
    }
  ],
  "panchina": [
    {
      "id": 102,
      "nome": "Martinez Jo.",
      "ruolo": "P",
      "ordine": 1
    }
  ],
  "esclusi_motivo": [
    {
      "nome": "Sanchez",
      "ruolo": "A",
      "motivo": "INFORTUNATO (Lesione muscolare)"
    }
  ]
}
```

---

### 4.3 R3: Indice Moneyball (Backend Python & Pipeline Integration)

#### Metric Definitions
1. **Expected Goals ($xG$)**: Quality and volume of chances generated.
2. **Expected Assists ($xA$)**: Quality and volume of key passes leading to shots.
3. **Moneyball Index ($MI$)**:
   $$MI = \frac{(xG \cdot 3.0) + (xA \cdot 1.0) + (\text{FM} - 5.0) \cdot 2.0}{\max(1, \text{PrezzoTarget})}$$
   Normalized to a 0–100 scale:
   $$MI_{\text{norm}} = \min\left(100.0, \max\left(0.0, \frac{MI - MI_{\min}}{MI_{\max} - MI_{\min}} \cdot 100\right)\right)$$
4. **Undervalued Asset Tier**:
   - `"SOTTOVALUTATO (Moneyball Bargain)"`: $MI_{\text{norm}} \ge 75$ and $\text{PrezzoTarget} \le 25$.
   - `"EQUILIBRATO (Fair Value)"`: $40 \le MI_{\text{norm}} < 75$.
   - `"SOPRAVVALUTATO (Premium/Hype)"`: $MI_{\text{norm}} < 40$ and $\text{PrezzoTarget} \ge 35$.

#### Extended Player Model Schema
```json
{
  "id": 5585,
  "nome": "Malen",
  "squadra": "Roma",
  "squadra_code": "ROM",
  "ruolo": "A",
  "ruolo_mantra": "pc",
  "qa": 38,
  "qi": 34,
  "fvm_1000": 450,
  "prezzo_target": 225,
  "prezzo_max": 281,
  "tier": "1 Top Assoluto (1° Slot)",
  "piazzati": "1° Rigorista / Perno Attacco Roma",
  "mod_rating": "",
  "mv": 8.25,
  "fm": 15.5,
  "stats": {
    "partite_a_voto": 2,
    "media_voto": 8.25,
    "fantamedia": 15.5,
    "gol": 5,
    "assist": 0,
    "xg": 4.12,
    "xa": 0.85,
    "xg_90": 2.06,
    "xa_90": 0.42,
    "moneyball_index": 88.5,
    "undervalued_status": "SOTTOVALUTATO (Moneyball Bargain)"
  }
}
```

---

## 5. Concrete Mock User Rosters & Test Fixtures

### 5.1 Mock Roster 1: Balanced Meta Squad (`tests/fixtures/roster_balanced.json`)
25 players covering standard 500-budget distribution:
- **Portieri (3)**: Sommer (48), Martinez Jo. (1), Di Gennaro (1)
- **Difensori (8)**: Dimarco (40), Bremer (32), Buongiorno (20), Gosens (16), Beukema (10), Coco (9), Luperto (5), Delprato (4)
- **Centrocampisti (8)**: Calhanoglu (45), Pulisic (45), Man (20), Nico Paz (12), Ederson (17), Frendrup (8), Gaetano (10), Maldini (8)
- **Attaccanti (6)**: Lautaro Martinez (170), Retegui (90), Castro (35), Lucca (30), Bonny (12), Cutrone (10)

### 5.2 Mock Roster 2: Budget Attack Heavy Squad (`tests/fixtures/roster_attack_heavy.json`)
3 Top Attackers enabled by low-cost goalkeeper trio:
- **Portieri (3)**: Milinkovic-Savic (16), Turati (10), Vasquez (7)
- **Difensori (8)**: Bellanova (22), Tavares (14), Dorgu (8), Gatti (15), Kolasinac (8), Vasquez (5), Vogliacco (5), Coco (9)
- **Centrocampisti (8)**: Zaccagni (40), Koopmeiners (42), Orsolini (25), Brescianini (7), Colpani (15), Pasalic (15), Man (20), Nico Paz (12)
- **Attaccanti (6)**: Lautaro Martinez (170), Vlahovic (150), Retegui (90), Pinamonti (25), Mosquera (10), Krstovic (18)

### 5.3 Mock Roster 3: Injury / Suspension Edge Case (`tests/fixtures/roster_edge_cases.json`)
Testing automatic bench substitution and exclusions:
- Injured player: Buchanan (D, Inter) -> must not be in starting XI.
- Suspended player: Pogba (C, Juve) -> must not be in starting XI.
- Ballottaggio player: Dumfries / Darmian -> starting XI based on percentage.

---

## 6. Verification Suite & Acceptance Test Blueprint

| Test Suite | Scope | Key Assertions |
|---|---|---|
| `test_data_integrity.py` | Pipeline & Datasets | Exit 0, 20 teams (Como, Parma, Venezia in; Salernitana, Sassuolo, Frosinone out), 588+ players, 380 matches |
| `test_max_bid.py` | R1 Frontend/Widget | Mathematical correctness of remaining credits, slot reservations, rival max bid calculation |
| `test_lineup_logic.py` | R2 Best Lineup | Valid modules (3-4-3, 3-5-2, 4-3-3, etc.), zero injured/suspended in starting XI, correct defense modifier bonus |
| `test_moneyball.py` | R3 Moneyball Metrics | xG, xA, Moneyball index calculation, non-corruption of base schema |

---
