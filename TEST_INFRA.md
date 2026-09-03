# Test Infrastructure & Strategy Specification
## Fantacalcio 2026/2027 Advanced Suite

**Document Version:** 2.0.0  
**Target Environment:** macOS / Linux (Python 3.9+ Zero External Dependencies)  
**Author:** E2E Test Architect Agent  
**Status:** Authoritative Test Architecture & Coverage Specification  

---

## 1. Test Architecture & Multi-Tier Methodology

The test infrastructure for the **Fantacalcio 2026/2027 Advanced Suite** provides comprehensive, genuine, opaque-box automated test suites designed according to standard engineering principles.

```
+---------------------------------------------------------------------------------------+
|                                ROOT ACCEPTANCE TEST SUITES                            |
|                                                                                       |
|  1. test_data_integrity.py (Pipeline Data Integrity Acceptance)                       |
|     - Pipeline Execution (exit code 0)                                                |
|     - All Data Artifacts Existence & Non-Emptiness in data/ (JSON + CSV)              |
|     - Strict 2026/2027 Team Roster (Como, Parma, Venezia in; Relegated out)           |
|     - Player Quotazioni, Role Partition, and Pricing Scaling (500 budget)             |
|     - 10-Match Probable Lineups Invariants (11 starters, 1 GK, bench)                  |
|     - 38-Giornate / 380-Match Calendar Symmetry Invariants                            |
|                                                                                       |
|  2. test_lineup_logic.py (Best Lineup & Acceptance Criteria Acceptance)                |
|     - All 7 Formations Validation (3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1)    |
|     - Strict Exclusion of Injured and Suspended Players (never fielded)               |
|     - Exact Modificatore Difesa Calculation (+0, +1, +3, +6 for >= 4 defenders)       |
|     - Dataset Structure Preservation (xG, xA, Moneyball Index without corruption)     |
|     - CLI Execution (best_lineup.py exit code 0)                                      |
+---------------------------------------------------------------------------------------+
                                           |
  +----------------------------------------+----------------------------------------+
  |                                        |                                        |
+--------------------------+  +--------------------------+  +-------------------------------+
|  Lineup Optimizer E2E    |  |  Moneyball Backend E2E   |  |   Auction Max Bid E2E         |
| (test_lineup_optimizer)  |  | (test_moneyball_metrics) |  |  (test_auction_max_bid.py)    |
+--------------------------+  +--------------------------+  +-------------------------------+
| - T1: Feature Coverage   |  | - Schema Validation      |  | - User Max Bid Formula        |
| - T2: Boundary & Corner  |  | - Outfield xG/xA > 0     |  | - Rival Ceiling Formula       |
| - T3: Combinations       |  | - Moneyball Index (0-100)|  | - Winning Bid Threshold       |
| - T4: Real Archetypes    |  | - Backwards Compatibility|  | - Role Minimum Reserves       |
|   (Balanced, Mod, Attack,|  | - Role Formula Math      |  | - Frontend JS Equivalence     |
|    Wonderkids, Emergency)|  |                          |  |   (dashboard/index.html)      |
+--------------------------+  +--------------------------+  +-------------------------------+
```

---

## 2. Test Suites Inventory & Coverage Breakdown

| Test Suite File | Scope | Test Classes | Test Count | Status |
|---|---|---|---|---|
| `test_lineup_logic.py` | Root Acceptance Suite: Lineup Logic, Modificatore, Injury Exclusion, Schema Preservation | 5 | 7 | PASS |
| `test_data_integrity.py` | Root Acceptance Suite: Data Pipeline, Roster Validation, File Artifacts | 6 | 8 | PASS |
| `tests/test_lineup_optimizer.py` | 4-Tier Lineup Optimizer E2E Suite: Formations, Modificatore, Goalkeeper Pairing, Squad Archetypes | 4 | 11 | PASS |
| `tests/test_moneyball_metrics.py` | Moneyball Index & Advanced Metrics: Schema Validation, xG/xA Distribution, Backwards Compatibility | 4 | 11 | PASS |
| `tests/test_auction_max_bid.py` | Auction Mathematical Engine: Max Bid Invariant, Rival Ceiling, Winning Bid, Role Reserves, Dashboard JS | 4 | 10 | PASS |
| `tests/test_tier1_feature_coverage.py` | Pipeline Tier 1: Feature Coverage (Registry, Models, Parsers, Exporters, Validators) | 8 | 48 | PASS |
| `tests/test_tier2_boundary_corner.py` | Pipeline Tier 2: Boundary & Corner Cases (Missing files, Zero stats, Corrupted records) | 4 | 12 | PASS |
| `tests/test_tier3_combinations.py` | Pipeline Tier 3: Cross-Feature Combinations (Pairwise CLI, Lineup & Player cross-ref) | 4 | 12 | PASS |
| `tests/test_tier4_real_world.py` | Pipeline Tier 4: Real-World Scenarios (Auction draft simulation, Matchday lineup export) | 4 | 7 | PASS |
| `tests/test_moneyball.py` | Data Ingestion & Model Integration for Moneyball fields | 3 | 7 | PASS |
| **TOTAL** | **Full Automated Test Suite** | **46** | **133** | **100% PASS** |

---

## 3. Detailed Acceptance Criteria & Invariant Mapping

### 3.1 Valid Formations Invariant
- **Rule**: Exactly 7 official formations supported: `3-4-3`, `3-5-2`, `4-3-3`, `4-4-2`, `4-5-1`, `5-3-2`, `5-4-1`.
- **Invariants**:
  - Exactly 1 Goalkeeper (`P`) fielded.
  - Number of defenders $\in \{3, 4, 5\}$.
  - Number of midfielders $\in \{3, 4, 5\}$.
  - Number of forwards $\in \{1, 2, 3\}$.
  - Starters sum $1 + D + C + A = 11$.
- **Verification**: `test_lineup_logic.py:TestValidFormationsGeneration`, `tests/test_lineup_optimizer.py:TestTier1FeatureCoverage`.

### 3.2 Injured & Suspended Player Exclusion Invariant
- **Rule**: A player with `is_injured=True`, `infortunato=True`, `is_suspended=True`, `squalificato=True`, or presence in probable lineups injury list must NEVER be fielded as starter or bench.
- **Verification**: `test_lineup_logic.py:TestInjuredAndSuspendedExclusion`, `tests/test_lineup_optimizer.py:TestTier2BoundaryCornerCases`, `tests/test_lineup_optimizer.py:TestTier4RealWorldScenarios`.

### 3.3 Modificatore Difesa Mathematical Calculation
- **Rule**:
  - Applicable ONLY when $\ge 4$ defenders start. When $D < 4$, modifier bonus is strictly $0.0$.
  - Average computed from GK expected vote + top 3 highest defender votes: $Avg = \frac{GK + D_{(1)} + D_{(2)} + D_{(3)}}{4.0}$.
  - Bonus Brackets:
    - $Avg < 6.00 \implies +0.0$
    - $6.00 \le Avg < 6.50 \implies +1.0$
    - $6.50 \le Avg < 7.00 \implies +3.0$
    - $Avg \ge 7.00 \implies +6.0$
- **Verification**: `test_lineup_logic.py:TestDefenseModifierCalculation`, `tests/test_lineup_optimizer.py:TestTier2BoundaryCornerCases`.

### 3.4 Moneyball Index & xG/xA Schema Preservation
- **Rule**:
  - `data/players.json`, `data/players.csv`, and `data/players_db.json` must contain `xg`, `xa`, `xg_90`, `xa_90`, `moneyball_index`.
  - Outfield players must have non-empty/positive xG/xA values.
  - Moneyball Index must be strictly positive and bounded within $[20.0, 99.0]$.
  - Zero corruption of legacy fields (`id`, `nome`, `squadra`, `ruolo`, `qa`, `fvm_1000`, `prezzo_target`, `mv`, `fm`).
- **Verification**: `test_lineup_logic.py:TestJsonDatasetPreservation`, `tests/test_moneyball_metrics.py`.

### 3.5 Auction Max Bid & Rival Tracker Formula Invariants
- **Rule**:
  - $MaxBid = Budget_{rem} - (Slots_{rem} - 1)$ for $Slots_{rem} \ge 1$.
  - $RivalCeiling = RivalCredits - (25 - RivalSlots - 1)$.
  - $WinningBid = \min(UserMax, TopRivalCeiling + 1)$.
  - Role Minimum Reserve $= \sum \text{EmptySlots}(r) \times 1$.
  - Frontend JS equivalence in `dashboard/index.html`.
- **Verification**: `tests/test_auction_max_bid.py`.

---

## 4. Execution Commands

```bash
# 1. Run Root Lineup Logic Acceptance Suite
python3 test_lineup_logic.py

# 2. Run Root Data Pipeline Integrity Acceptance Suite
python3 test_data_integrity.py

# 3. Run Modular E2E Test Suite (All 118 tests in tests/)
python3 -m unittest discover tests

# 4. Run specific modular test files
python3 -m unittest tests/test_lineup_optimizer.py
python3 -m unittest tests/test_moneyball_metrics.py
python3 -m unittest tests/test_auction_max_bid.py
```
