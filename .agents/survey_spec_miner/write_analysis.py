import sys

analysis_content = """# SPECIFICATION ANALYSIS: FANTACALCIO 2026/2027 ADVANCED TOOLSUITE

**Author**: survey_spec_miner  
**Date**: 2026-09-02  
**Target Requirements**: R1 (Auction Max Price Calculator), R2 (Lineup Optimizer best_lineup.py), R3 (Moneyball Index)  
**Authoritative Sources**: `ORIGINAL_REQUEST.md`, `PROJECT.md`, `dashboard/index.html`, `src/goalkeeper_analyzer.py`, `src/models.py`, `src/parsers/lineups_parser.py`, `data/players.json`, `data/probabili_formazioni.json`.

---

## 1. Executive Summary & Domain Scope

The Fantacalcio 2026/2027 advanced toolsuite expands the automated pipeline into three decision-support engines:
1. **R1: Auction Max Price Calculator (`Prezzo Massimo`)**: A real-time, mathematically strict and strategic budget allocation engine for live auction drafting (10 teams, 500/1000 credits, 25 roster slots).
2. **R2: Lineup Optimizer (`best_lineup.py`)**: A tactical MILP (Mixed Integer Linear Programming) / combinatorial decision engine that computes the optimal starting XI and ordered bench across 7 valid Serie A formations (3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1), integrating probable lineups, titolarità %, injury/suspension exclusions, goalkeeper fixture matrices, and the Classic Defense Modifier formula.
3. **R3: Moneyball Index (`Expected Stats & Undervalued Gems`)**: An advanced statistical pipeline calculating Expected Goals ($xG$), Expected Assists ($xA$), Expected Fantamedia ($xFM$), Value Over Replacement Player ($VORP$), and a normalized Moneyball Value Index ($MVI$) to uncover undervalued transfer targets and market inefficiencies.

---

## 2. Requirement R1: Auction Max Price Calculator (Prezzo Massimo)

### 2.1 Mathematical Formulation & Invariants

#### League & User Parameters
- Total Initial Budget: $B_{tot} \in \\{500, 1000\\}$ (default: $500$ credits).
- User Current Remaining Credits: $B \in \\mathbb{N}_{\\ge 0}$.
- User Total Roster Size Target: $N = 25$ (Official composition: 3 Portieri, 8 Difensori, 8 Centrocampisti, 6 Attaccanti).
- User Filled Slots: $R = |R_P| + |R_D| + |R_C| + |R_A|$ where $R \\in [0, 25]$.
- User Remaining Empty Slots: $S = N - R = 25 - R$.
- Opponents: Set of rivals $\\mathcal{O} = \\{1, 2, \\dots, K\\}$ (in a 10-team league, $K = 9$).
- Opponent $i$ Remaining Credits: $O_i \\in \\mathbb{N}_{\\ge 0}$.
- Opponent $i$ Remaining Empty Slots: $S_{o,i} = N - |R_{o,i}|$.

#### Strict Minimum 1 Credit per Slot Invariant
In official Italian Fantacalcio rules, every player slot must be filled by spending at least 1 credit. No slot can be left empty, and no player can be bought for 0 credits.
Therefore, if a manager with $B$ credits and $S$ empty slots buys 1 player at price $P$:
1. The remaining budget becomes $B' = B - P$.
2. The remaining empty slots become $S' = S - 1$.
3. To legally fill the remaining $S - 1$ slots, the remaining budget must satisfy:
   $$B - P \\ge S - 1 \\iff P \\le B - (S - 1) = B - S + 1$$

#### Mathematical Formulations

##### 1. User Strict Mathematical Ceiling ($P_{strict\\_max}$)
The absolute maximum bid the user can legally make for a single player without violating the 1-credit-per-slot rule:
$$P_{strict\\_max}(B, S) = \\begin{cases}
0 & \\text{if } S \\le 0 \\text{ or } B < S \\\\
B - S + 1 & \\text{if } S \\ge 1 \\text{ and } B \\ge S
\\end{cases}$$

*Boundary Behavior*:
- When $S = 1$ (last empty slot): $P_{strict\\_max} = B - 1 + 1 = B$ (can spend all remaining credits).
- When $S = 25$ (start of auction, $B=500$): $P_{strict\\_max} = 500 - 25 + 1 = 476$ credits.
- When $S = 0$ (roster full): $P_{strict\\_max} = 0$ (cannot bid).
- When $B < S$: Insolvent state (error condition).

##### 2. Opponents' Strict Ceilings ($M_i$) and Highest Rival Ceiling ($M_{opp\\_max}$)
For each opponent $i \\in \\{1, \\dots, K\\}$:
$$M_i(O_i, S_{o,i}) = \\begin{cases}
0 & \\text{if } S_{o,i} \\le 0 \\text{ or } O_i < S_{o,i} \\\\
O_i - S_{o,i} + 1 & \\text{if } S_{o,i} \\ge 1 \\text{ and } O_i \\ge S_{o,i}
\\end{cases}$$
The highest competitive ceiling in the room is:
$$M_{opp\\_max} = \\max_{i \\in \\mathcal{O}} M_i(O_i, S_{o,i})$$
The second highest rival ceiling is:
$$M_{opp\\_second} = \\max_{j \\in \\mathcal{O} \\setminus \\{i^*\\}} M_j \\quad \\text{where } i^* = \\arg\\max_i M_i$$

##### 3. Guaranteed Winning Price (Prezzo di Certezza / Auction Dominance)
- If $P_{strict\\_max} > M_{opp\\_max}$: The user is the absolute wealthiest bidder for that slot in the entire league. The exact price to guarantee acquisition is:
  $$P_{guaranteed} = M_{opp\\_max} + 1$$
- If $P_{strict\\_max} \\le M_{opp\\_max}$: The user cannot guarantee winning against an all-in rival; user can only bid up to $P_{strict\\_max}$.

##### 4. Recommended Strategic Price ($P_{rec}$) & Safe Ceiling ($P_{safe\\_max}$)
Bidding $P_{strict\\_max}$ leaves 1 credit for all remaining slots, ruining squad depth. The strategic price calculator computes:
- **Role Target Budget Pool ($B_{role\\_target}$)**:
  - Portieri (3 slots): $7\\% \\cdot B_{tot} = 35$ cr (Range: $30 - 45$ cr)
  - Difensori (8 slots): $10\\% \\cdot B_{tot} = 50$ cr (Range: $40 - 60$ cr)
  - Centrocampisti (8 slots): $22\\% \\cdot B_{tot} = 110$ cr (Range: $100 - 125$ cr)
  - Attaccanti (6 slots): $61\\% \\cdot B_{tot} = 305$ cr (Range: $275 - 325$ cr)
- **Market Liquidity Inflation Index ($\\theta$)**:
  $$\\theta = \\frac{\\sum_{i \\in \\mathcal{O}} O_i + B - \\left(\\sum_{i \\in \\mathcal{O}} S_{o,i} + S\\right)}{\\sum_{p \\in \\text{Unassigned}} \\text{TargetPrice}_p}$$
- **Strategic Player Ceiling ($P_{strat\\_max}$)**:
  $$P_{strat\\_max}(p) = \\min\\left( P_{strict\\_max}, \\; \\text{round}\\left( \\text{PrezzoTarget}(p) \\cdot \\text{clamp}(\\theta, 0.8, 1.3) \\right) \\right)$$
- **Role Reserve Buffer**:
  To ensure the remaining $S - 1$ slots have balanced quality:
  $$P_{safe\\_max}(p) = \\min\\left( P_{strict\\_max}, \\; B - \\sum_{r \\in \\{P,D,C,A\\}} S_r \\cdot \\text{MinQualityFloor}(r) + \\text{MinQualityFloor}(ruolo(p)) \\right)$$
  where $\\text{MinQualityFloor} = \\{P: 3, D: 2, C: 3, A: 8\\}$.

---

## 3. Requirement R2: Lineup Optimizer (`best_lineup.py`)

### 3.1 Tactical Formations & Domain Rules

#### Valid Tactical Formations ($\\mathcal{M}$)
Classic Fantacalcio permits exactly 7 official tactical formations composed of 1 Goalkeeper ($n_P = 1$) and 10 outfielders ($n_D + n_C + n_A = 10$):
1. **3-4-3**: $n_D = 3, n_C = 4, n_A = 3$ (Offensive)
2. **3-5-2**: $n_D = 3, n_C = 5, n_A = 2$ (Midfield Dominance)
3. **4-3-3**: $n_D = 4, n_C = 3, n_A = 3$ (Balanced Attack + Modificatore eligible)
4. **4-4-2**: $n_D = 4, n_C = 4, n_A = 2$ (Classic Balanced + Modificatore eligible)
5. **4-5-1**: $n_D = 4, n_C = 5, n_A = 1$ (Midfield Control + Modificatore eligible)
6. **5-3-2**: $n_D = 5, n_C = 3, n_A = 2$ (Defensive Fortress + Modificatore eligible)
7. **5-4-1**: $n_D = 5, n_C = 4, n_A = 1$ (Catenaccio + Modificatore eligible)

Any other formation (e.g. 2-5-3, 3-3-4, 4-2-4, 6-3-1) is strictly invalid in Serie A Classic rules and must be rejected.

### 3.2 Probable Lineups (`probabili_formazioni.json`) Integration

#### Starter Probability & Player Status
Let $T(p) \\in [0.0, 1.0]$ denote the titolarità probability of player $p$:
- **Infortunati / Squalificati / Fuori Rosa**:
  $$p \\in \\text{Infortunati} \\cup \\text{Squalificati} \\implies T(p) = 0.0 \\quad (\\text{Strictly Excluded from XI})$$
- **Listed Starters (`status == 'STARTER'`)**:
  $$T(p) = \\frac{\\text{probabilita}}{100} \\quad (\\text{typically } 0.70 \\le T(p) \\le 0.95)$$
- **Ballottaggio**:
  $$T(p) = \\frac{\\text{ballottaggio\\_percentage}}{100} \\quad (\\text{typically } 0.40 \\le T(p) \\le 0.60)$$
- **Bench / Reserve (`status == 'BENCH'`)**:
  $$T(p) = 0.20 \\cdot \\frac{\\text{probabilita}}{100} \\quad (\\text{substitute appearance probability})$$

### 3.3 Goalkeeper Fixture Grid & Expected Conceded Goals ($xGC$)

#### Matrix Difficulty Classification
Given Goalkeeper team $T_g$ playing at location $Loc \\in \\{\\text{Home}, \\text{Away}\\}$ against Opponent $T_{opp}$:
- Opponent Attack Tier $OAT(T_{opp}) \\in \\{1: \\text{Top}, 2: \\text{Good}, 3: \\text{Mid}, 4: \\text{Low}\\}$:
  - Tier 1: Inter, Atalanta, Milan, Juventus, Napoli
  - Tier 2: Roma, Lazio, Fiorentina, Bologna
  - Tier 3: Torino, Genoa, Monza, Parma, Udinese, Cagliari
  - Tier 4: Empoli, Verona, Lecce, Como, Venezia
- Match Difficulty Level $\\text{Diff}_{GK}$:
  $$\\text{Diff}_{GK} = \\begin{cases}
  1 \\; (\\text{FACILE}) & \\text{if } Loc = \\text{Home} \\text{ and } OAT \\in \\{3, 4\\} \\\\
  2 \\; (\\text{MEDIA}) & \\text{if } (Loc = \\text{Home} \\text{ and } OAT \\in \\{1, 2\\}) \\lor (Loc = \\text{Away} \\text{ and } OAT \\in \\{3, 4\\}) \\\\
  3 \\; (\\text{DIFFICILE}) & \\text{if } Loc = \\text{Away} \\text{ and } OAT \\in \\{1, 2\\}
  \\end{cases}$$
- Expected Goals Conceded ($xGC$):
  $$xGC(p) = 0.55 \\cdot \\text{Diff}_{GK} + 0.15 \\cdot \\frac{10 - \\text{DEF\\_RATING}(T_g)}{4.0}$$
- Expected Clean Sheet Probability:
  $$P(\\text{CleanSheet}) = \\max\\left(0.05, \\; 0.60 - 0.18 \\cdot \\text{Diff}_{GK}\\right)$$

### 3.4 Player Expected Fantavoto ($E[FV]$) Formulation

#### 1. Goalkeeper Expected Score:
$$E[V_{GK}] = MV(p) + 0.15 \\cdot (2 - \\text{Diff}_{GK})$$
$$E[FV_{GK}] = T(p) \\cdot \\Big( E[V_{GK}] - 1.0 \\cdot xGC(p) + 1.0 \\cdot P(\\text{CleanSheet}_p) + 3.0 \\cdot P(\\text{PenaltySave}_p) \\Big)$$

#### 2. Outfield Players ($D, C, A$):
Let $E[V_p]$ be the expected pure match rating (pagella grade):
$$E[V_p] = MV(p) + \\Delta_{loc}(Loc) + \\Delta_{opp}(T_{opp})$$
where:
- $\\Delta_{loc}(\\text{Home}) = +0.10$, $\\Delta_{loc}(\\text{Away}) = -0.10$.
- $\\Delta_{opp} = \\frac{10 - \\text{DEF\\_RATING}(T_{opp})}{10} \\cdot 0.30$.

The Expected Fantavoto is:
$$E[FV_p] = T(p) \\cdot \\Big( E[V_p] + 3.0 \\cdot xG_p + 1.0 \\cdot xA_p + \\text{SetPieceBonus}_p - 0.5 \\cdot P(\\text{Yellow}_p) - 1.0 \\cdot P(\\text{Red}_p) \\Big) + (1 - T(p)) \\cdot E[FV_{\\text{sub}}]$$
where $\\text{SetPieceBonus} = +0.40$ if 1st penalty taker, $+0.15$ if corners/free kicks.

### 3.5 Modificatore Difesa: Exact Formula & Bonus Tables

#### Eligibility Invariant
The defense modifier is active **if and only if**:
1. The tactical formation contains **at least 4 defenders** ($n_D \\ge 4 \\implies$ modules 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1).
2. The goalkeeper and at least 3 defenders receive a valid pure rating (voto puro $\\ge 1.0$).

#### Calculation Formula
Take the Goalkeeper's expected pure grade $E[V_{GK}]$ and the 3 highest expected pure grades among starting defenders $E[V_{D,(1)}] \\ge E[V_{D,(2)}] \\ge E[V_{D,(3)}]$:
$$M_{dif} = \\frac{E[V_{GK}] + E[V_{D,(1)}] + E[V_{D,(2)}] + E[V_{D,(3)}]}{4}$$

#### Official Classic Modificatore Bonus Table (Standard Rule per ORIGINAL_REQUEST.md)
| Defense Average ($M_{dif}$) | Bonus Points Added to Total |
|-----------------------------|-----------------------------|
| $M_{dif} < 6.00$            | **0**                       |
| $6.00 \\le M_{dif} < 6.50$   | **+1**                      |
| $6.50 \\le M_{dif} < 7.00$   | **+3**                      |
| $M_{dif} \\ge 7.00$          | **+6**                      |

#### Granular 6-Tier Modificatore Table (Dashboard & Extended Leagues)
| Defense Average ($M_{dif}$) | Bonus Points Added to Total |
|-----------------------------|-----------------------------|
| $M_{dif} < 6.00$            | **0**                       |
| $6.00 \\le M_{dif} < 6.25$   | **+1**                      |
| $6.25 \\le M_{dif} < 6.50$   | **+2**                      |
| $6.50 \\le M_{dif} < 6.75$   | **+3**                      |
| $6.75 \\le M_{dif} < 7.00$   | **+4**                      |
| $7.00 \\le M_{dif} < 7.25$   | **+5**                      |
| $M_{dif} \\ge 7.25$          | **+6**                      |

### 3.6 Tactical Optimization Algorithm & Bench Assembly

For each formation $m = (n_D, n_C, n_A) \\in \\mathcal{M}$:
1. Best Goalkeeper: $p_{GK}^* = \\arg\\max_{p \\in \\mathcal{R}_P} E[FV(p)]$.
2. Starters Selection:
   - Out of 8 defenders in $\\mathcal{R}_D$, select the subset $D_m \\subset \\mathcal{R}_D$ ($|D_m| = n_D$) maximizing $\\sum_{p \\in D_m} E[FV(p)] + \\mathbb{I}(n_D \\ge 4) \\cdot \\text{BonusMod}(M_{dif})$.
   - Out of 8 midfielders in $\\mathcal{R}_C$, select top $n_C$ with highest $E[FV]$.
   - Out of 6 attackers in $\\mathcal{R}_A$, select top $n_A$ with highest $E[FV]$.
3. Formation Total Expected Score:
   $$Score(m) = E[FV_{GK}^*] + \\sum_{p \\in D_m} E[FV(p)] + \\sum_{p \\in C_m} E[FV(p)] + \\sum_{p \\in A_m} E[FV(p)] + \\text{ModBonus}(m)$$
4. Global Optimal Formation:
   $$m^* = \\arg\\max_{m \\in \\mathcal{M}} Score(m)$$
5. Bench Ordering (Panchina Ordinata):
   - 2 Goalkeepers sorted by $E[FV]$
   - Remaining Defenders sorted by $E[FV]$ (top 2-3)
   - Remaining Midfielders sorted by $E[FV]$ (top 2-3)
   - Remaining Attackers sorted by $E[FV]$ (top 2-3)

---

## 4. Requirement R3: Moneyball Index & Undervalued Gems

### 4.1 Advanced Statistical Metrics Definition

1. **Expected Goals ($xG$)**:
   The conditional probability that an unblocked shot results in a goal given contextual attributes:
   $$xG = \\sum_{k \\in \\text{Shots}} P(\\text{Goal}_k \\mid \\text{Context})$$
   where features include shot distance, angle, header vs foot, open play vs corner/free-kick, big chance indicator.
2. **Expected Assists ($xA$)**:
   The probability that a completed key pass results in a goal based on the quality of the chance provided to the shooter.
3. **Per-90 Normalization**:
   $$xG90 = \\frac{xG}{\\text{MinutiGiocati}} \\cdot 90, \\quad xA90 = \\frac{xA}{\\text{MinutiGiocati}} \\cdot 90$$
4. **Projected Expected Fantamedia ($xFM$)**:
   $$xFM(p) = MV(p) + 3.0 \\cdot xG90_p + 1.0 \\cdot xA90_p - 0.5 \\cdot \\text{Ammonizioni90}_p - 1.0 \\cdot \\text{Espulsioni90}_p$$

### 4.2 Moneyball Valuation Formulations

#### Value Over Replacement Player ($VORP_{fanta}$)
Defines the marginal expected fantavoto above a replacement-level player (cost = 1 cr):
$$VORP(p) = \\max\\left(0, \\; xFM(p) - BV_{\\text{ruolo}(p)}\right)$$
where Role Baselines are:
- $BV_P = 4.50$
- $BV_D = 5.60$
- $BV_C = 5.85$
- $BV_A = 6.20$

#### Moneyball Value Index ($MVI$)
Measures performance yield per credit invested:
$$MVI(p) = \\frac{VORP(p) \\times 100}{\\max(1, \\; \\text{PrezzoTarget}(p))}$$

#### Moneyball Composite Score ($S_{MB} \\in [0, 100]$)
$$S_{MB}(p) = 0.50 \\cdot \\text{YieldScore}(p) + 0.30 \\cdot \\text{RegressionDelta}(p) + 0.20 \\cdot \\text{TacticalPositionAdvantage}(p)$$
where:
- $\\text{YieldScore}(p) = \\min\\left(100, \\; \\frac{VORP(p)}{\\text{PrezzoTarget}(p)^{0.55}} \\times 25\\right)$.
- $\\text{RegressionDelta}(p) = \\min\\left(100, \\; \\max\\left(0, \\; 50 + 20 \\cdot ((xG + xA) - (\\text{Gol} + \\text{Assist}))\\right)\\right)$ (high positive delta $\\implies$ unlucky finisher/creator due for mean reversion).
- $\\text{TacticalPositionAdvantage}(p) = 20$ if defender plays as wingback/winger, $20$ if midfielder plays as forward, $0$ otherwise.

### 4.3 Undervalued Gem Detection Rules ("Giocatori Sottovalutati")

A player is classified as an **"Undervalued Gem"** (`is_undervalued = True`) if they satisfy at least one of these 4 conditions:
1. **Bad Luck Striker / Winger**: Ruolo $\\in \\{C, A\\}$, $xG - \\text{Gol} \\ge 1.5$, $xG90 \\ge 0.25$, and $\\text{PrezzoTarget} \\le 20$.
2. **Hidden Playmaker**: Ruolo $\\in \\{D, C\\}$, $xA - \\text{Assist} \\ge 1.5$, $xA90 \\ge 0.20$, and $\\text{PrezzoTarget} \\le 15$.
3. **Out-of-Position Bug ("Bug del Listone")**: Ruolo = `D` with offensive heatmaps / playing winger, or Ruolo = `C` playing second striker, with $xG90 + xA90 \\ge 0.30$ and $QA \\le 15$.
4. **Super-Value Regular**: $MVI(p) \\ge 15.0$ and $\\text{is\\_starter} = \\text{True}$.

---

## 5. Discovered Features & Edge Cases

## Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | R1: Auction Calculator | Strict Max Price ($P_{strict\\_max}$) | Computes exact legal ceiling leaving min 1 cr per remaining slot | Budget $B$, Remaining Slots $S$ | Integer max bid ($B - S + 1$) | Returns 0 if $S \\le 0$ or $B < S$; throws if negative | `dashboard/index.html` & `ORIGINAL_REQUEST.md` |
| 2 | R1: Auction Calculator | Rival Max Bid Tracker | Computes maximum legal bids for all $K$ opponents in real time | Rivals list $[(O_i, S_{o,i})]$ | List of max bids, $M_{opp\\_max}$, $M_{opp\\_second}$ | Clamps negative credits to 0, handles full rosters | `dashboard/index.html` |
| 3 | R1: Auction Calculator | Guaranteed Purchase Price | Computes bid required to guarantee winning player against room | $P_{strict\\_max}, M_{opp\\_max}$ | Guaranteed price $M_{opp\\_max} + 1$ or Unreachable flag | Flags if user cannot outbid richest opponent | Mathematical analysis |
| 4 | R1: Auction Calculator | Strategic Recommended Price | Calculates optimal bid balancing player FVM, inflation $\\theta$, role quality floor | Player FVM, $B$, $S$, Market Liquidity | Recommended target price & safe max ceiling | Clamps between 1 and $P_{strict\\_max}$ | Domain analysis |
| 5 | R2: Lineup Optimizer | Tactical Module Validator | Validates lineup against 7 official Serie A formations (3-4-3..5-4-1) | Formation string (e.g. '4-3-3') | Boolean validity, role counts | Raises `ValueError` for invalid modules (e.g. 2-5-3) | Serie A / FG Regulation |
| 6 | R2: Lineup Optimizer | Injury & Suspension Filter | Strictly excludes injured and suspended players from starting XI | `probabili_formazioni.json` status | Filtered candidate pool ($T(p) = 0.0$) | Logs warning if key player unavailable | `src/models.py` & `lineups.json` |
| 7 | R2: Lineup Optimizer | Titolarità & Ballottaggio Weighting | Blends starter probability with expected grade and sub appearance | Lineup starter/bench status, ballottaggi % | Effective Titolarità $T(p) \\in [0.0, 1.0]$ | Defaults to 0.90 for starters, 0.20 for bench if % missing | `src/parsers/lineups_parser.py` |
| 8 | R2: Lineup Optimizer | Goalkeeper Grid Difficulty | Classifies match into Facile (1), Media (2), Difficile (3) based on opponent tier & venue | GK team, Opponent, Home/Away | Match tier, $xGC$, Clean Sheet prob | Handles unknown team with default Tier 2 | `src/goalkeeper_analyzer.py` |
| 9 | R2: Lineup Optimizer | Classic Modificatore Difesa | Evaluates GK + 3 best defenders average and computes +1/+3/+6 bonus | Starters ratings ($n_D \\ge 4$) | Defense Average $M_{dif}$, Bonus Points | Returns 0 bonus if $n_D < 4$ or $M_{dif} < 6.00$ | Classic Regolamento FG |
| 10 | R2: Lineup Optimizer | Best XI MILP Optimizer | Optimizes selection across all 7 formations to maximize total Expected Fantavoto | 25-player roster, lineups, fixtures | Optimal starting XI, best formation, expected score | Handles missing positions with penalty fallback | Combinatorial solver |
| 11 | R2: Lineup Optimizer | Ordered Bench Generator | Assembles ordered substitution bench by role (2 P, 2-3 D, 2-3 C, 2-3 A) | Non-starting roster players | Formatted 14-man ordered bench | Fills all available non-starting slots | Serie A Matchday Protocol |
| 12 | R3: Moneyball Module | xG & xA Ingestion & Parser | Extracts shot quality and assist creation rates | Player stats or model feeds | Float $xG, xA, xG90, xA90$ | Defaults to 0.0 if missing | Analytics specification |
| 13 | R3: Moneyball Module | Projected Fantamedia ($xFM$) | Projects expected true performance removing finishing luck | $MV, xG90, xA90$, cards | Float $xFM$ | Clamps $xFM$ within $[1.0, 15.0]$ | Moneyball formulation |
| 14 | R3: Moneyball Module | Moneyball Value Index ($MVI$) | Computes VORP per credit spent to rank acquisition efficiency | $xFM, BV_{role}, \\text{PrezzoTarget}$ | Float $MVI$ score | Uses denominator max(1, price) to prevent div-by-zero | Sabermetric formulation |
| 15 | R3: Moneyball Module | Undervalued Gem Classifier | Flags undervalued players with specific regression/tactical tags | Player metrics, $QA$, Price | Boolean `is_undervalued`, reason tag | Non-breaking extension of `players.json` schema | Domain criteria |

## Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | R1: Max Price | $S = 1$ (Last slot), $B = 15$ | $P_{strict\\_max} = 15 - 1 + 1 = 15$. User can spend all remaining credits. |
| 2 | R1: Max Price | $S = 25$ (Empty roster), $B = 500$ | $P_{strict\\_max} = 500 - 25 + 1 = 476$. Preserves 24 cr for remaining 24 slots. |
| 3 | R1: Max Price | $S = 0$ (Full roster) | $P_{strict\\_max} = 0$. User blocked from bidding. |
| 4 | R1: Max Price | $B < S$ (Insolvent roster, e.g. $B=2, S=3$) | Algorithm flags critical deficit; max bid = 0. |
| 5 | R1: Max Price | Opponent $O_j = 0, S_{o,j} = 2$ | $M_j = 0$. Opponent cannot bid. |
| 6 | R1: Max Price | Rival $M_{opp\\_max} \\ge P_{strict\\_max}$ | User notified that guaranteed purchase is impossible if rival commits max. |
| 7 | R2: Lineup Optimizer | Formation with 3 Defenders (3-4-3 or 3-5-2) with defense average 7.50 | Modificatore bonus is **0** points (modificatore strictly requires $\\ge 4$ defenders). |
| 8 | R2: Lineup Optimizer | Player listed in `infortunati` or `squalificati` | Player assigned $T(p) = 0.0$ and excluded from starting XI even if high average. |
| 9 | R2: Lineup Optimizer | 4 Defenders with ratings $[6.5, 6.5, 6.0, 5.0]$, GK rating $6.0$ | Top 3 defs $[6.5, 6.5, 6.0]$, GK $6.0$. $M_{dif} = (6.0 + 6.5 + 6.5 + 6.0)/4 = 6.25 \\implies +1$ bonus in Classic, $+2$ in 6-Tier. |
| 10 | R2: Lineup Optimizer | Goalkeeper playing Away vs Inter (Tier 1) | Classified as Difficile (Tier 3), $xGC \\approx 1.8$, clean sheet prob $\\approx 6\\%$. |
| 11 | R2: Lineup Optimizer | Roster has fewer than 11 available players due to injuries | System schiera all available players and flags shortfall with virtual penalty. |
| 12 | R3: Moneyball | Player with 0 minutes / 0 appearances | $xG90, xA90 = 0.0$, $xFM = MV$ or baseline, $MVI = 0.0$, not crashing on div-by-zero. |
| 13 | R3: Moneyball | Striker with 0 goals but $3.5$ xG and target price 12 cr | Classified as `is_undervalued = True` with tag `"High xG regression candidate"`. |
| 14 | R3: Moneyball | Target price = 0 or missing | Denominator clamped to 1 credit: $\\max(1, \\text{price})$, avoiding ZeroDivisionError. |

---

## 6. Schema Specifications & API Contracts

### 6.1 `data/players.json` Schema Extension
Existing keys (`id`, `nome`, `squadra`, `ruolo`, `qa`, `qi`, `fvm_1000`, `prezzo_target`, `prezzo_max`, `stats`) are preserved 100% backward-compatibly, adding:
```json
{
  "xg": 3.82,
  "xa": 2.14,
  "xg90": 0.44,
  "xa90": 0.25,
  "xfm": 7.62,
  "vorp": 1.42,
  "moneyball_index": 78.5,
  "is_undervalued": true,
  "undervalued_reason": "High xG regression candidate"
}
```

### 6.2 `best_lineup.py` CLI & Function Contract
- **Function**: `optimize_lineup(roster_path: str, lineups_path: str, fixtures_path: str, use_defense_modifier: bool = True) -> dict`
- **Output JSON Structure**:
```json
{
  "matchday": 1,
  "formation": "4-3-3",
  "expected_total_score": 74.85,
  "defense_modifier": {
    "active": true,
    "average": 6.375,
    "bonus": 1.0,
    "contributing_ratings": {
      "goalkeeper": {"nome": "Di Gregorio", "voto": 6.5},
      "defenders": [
        {"nome": "Dimarco", "voto": 6.5},
        {"nome": "Buongiorno", "voto": 6.5},
        {"nome": "Bremer", "voto": 6.0}
      ]
    }
  },
  "starters": [
    {"ruolo": "P", "nome": "Di Gregorio", "squadra": "Juventus", "expected_fv": 5.85, "titolarita_pct": 95},
    {"ruolo": "D", "nome": "Dimarco", "squadra": "Inter", "expected_fv": 6.80, "titolarita_pct": 90},
    {"ruolo": "D", "nome": "Buongiorno", "squadra": "Napoli", "expected_fv": 6.20, "titolarita_pct": 90},
    {"ruolo": "D", "nome": "Bremer", "squadra": "Juventus", "expected_fv": 6.10, "titolarita_pct": 90},
    {"ruolo": "D", "nome": "Tavsan", "squadra": "Verona", "expected_fv": 5.75, "titolarita_pct": 80},
    {"ruolo": "C", "nome": "Pulisic", "squadra": "Milan", "expected_fv": 7.40, "titolarita_pct": 90},
    {"ruolo": "C", "nome": "Zaccagni", "squadra": "Lazio", "expected_fv": 7.10, "titolarita_pct": 85},
    {"ruolo": "C", "nome": "Man", "squadra": "Parma", "expected_fv": 6.65, "titolarita_pct": 85},
    {"ruolo": "A", "nome": "Lautaro", "squadra": "Inter", "expected_fv": 8.50, "titolarita_pct": 95},
    {"ruolo": "A", "nome": "Vlahovic", "squadra": "Juventus", "expected_fv": 8.10, "titolarita_pct": 90},
    {"ruolo": "A", "nome": "Lookman", "squadra": "Atalanta", "expected_fv": 7.80, "titolarita_pct": 85}
  ],
  "bench": [
    {"ruolo": "P", "nome": "Perin", "squadra": "Juventus", "expected_fv": 1.0},
    {"ruolo": "D", "nome": "Kolasinac", "squadra": "Atalanta", "expected_fv": 5.60},
    {"ruolo": "D", "nome": "Gatti", "squadra": "Juventus", "expected_fv": 5.50},
    {"ruolo": "C", "nome": "Frendrup", "squadra": "Genoa", "expected_fv": 6.00},
    {"ruolo": "C", "nome": "Pessina", "squadra": "Monza", "expected_fv": 5.90},
    {"ruolo": "A", "nome": "Castro", "squadra": "Bologna", "expected_fv": 6.50},
    {"ruolo": "A", "nome": "Lucca", "squadra": "Udinese", "expected_fv": 6.30}
  ]
}
```

### 6.3 Dashboard JavaScript Calculator Contract (`dashboard/index.html`)
- UI Input: Real-time user budget $B$, remaining user slots $S$, rival spend inputs.
- Output UI Elements:
  - `#user-max-bid`: $P_{strict\\_max} = \\max(1, B - S + 1)$
  - `#user-guaranteed-bid`: $M_{opp\\_max} + 1$ (if $P_{strict\\_max} > M_{opp\\_max}$)
  - `#rival-max-bid`: $O_i - S_{o,i} + 1$ per rival row
  - `#mod-bonus-display`: Modificatore bonus calculator (+1 to +6).
"""

with open('.agents/survey_spec_miner/analysis.md', 'w', encoding='utf-8') as f:
    f.write(analysis_content)

print("analysis.md generated successfully")
