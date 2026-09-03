# Handoff Report — Challenger 2 (Empirical Challenger)

**Milestone**: Adversarial Stress-Testing of Auction Max Price Calculator & Moneyball Data Pipeline  
**Author**: challenger_2  
**Date**: 2026-09-02T15:41:00+02:00  
**Verdict**: **APPROVE** (Auction Max Price Calculator & Moneyball Data Pipeline 100% Robust)

---

## 1. Observation

### A. Mathematical Edge Cases in Auction Max Price Calculation (`dashboard/index.html`)
Direct inspection of JavaScript logic in `dashboard/index.html` (lines 724–789, 868–906, 917–945):
- **User Max Single Bid Formula** (lines 727, 870):
  ```javascript
  const remainingCredits = totalBudget - userTotalSpent;
  const remainingSlots = 25 - totalCount;
  const maxBid = remainingSlots > 0 ? Math.max(1, (remainingCredits - (remainingSlots - 1))) : remainingCredits;
  ```
- **Rival Ceiling Formula** (lines 733–739, 876–882):
  ```javascript
  rivals.forEach(r => {
      const remSlots = 25 - r.slots;
      const rMax = remSlots > 0 ? Math.max(1, r.credits - (remSlots - 1)) : r.credits;
      if (rMax > topRivalCeiling) {
          topRivalCeiling = rMax;
          topRivalName = r.name;
      }
  });
  ```
- **Strategic Role Safety Reserves** (lines 742–755):
  ```javascript
  const limits = { P: 3, D: 8, C: 8, A: 6 };
  const remP = Math.max(0, limits.P - userRoster.P.length);
  const remD = Math.max(0, limits.D - userRoster.D.length);
  const remC = Math.max(0, limits.C - userRoster.C.length);
  const remA = Math.max(0, limits.A - userRoster.A.length);

  let otherRolesReserve = 0;
  if (p.ruolo === 'P') otherRolesReserve = remD + remC + remA + Math.max(0, remP - 1);
  else if (p.ruolo === 'D') otherRolesReserve = remP + remC + remA + Math.max(0, remD - 1);
  else if (p.ruolo === 'C') otherRolesReserve = remP + remD + remA + Math.max(0, remC - 1);
  else if (p.ruolo === 'A') otherRolesReserve = remP + remD + remC + Math.max(0, remA - 1);

  const safeMaxForRole = Math.max(1, remainingCredits - otherRolesReserve);
  ```
- **Evaluator Deficit Alert**:
  Lines 770–773 trigger `ATTENZIONE BUDGET` and prevent unsustainable bids whenever `currentBid > safeMaxForRole || currentBid > userMaxBid`.

### B. Moneyball Data Pipeline (`src/models.py`, `src/parsers/players_parser.py`, `src/storage/`)
Direct inspection of `src/parsers/players_parser.py` (lines 24–101):
- `cost = max(1, prezzo_target)` guarantees denominator strictly $\ge 1$.
- `35.0 / max(2, cost)` for goalkeepers with $FVM < 30$ guarantees divisor $\ge 2$, strictly preventing division-by-zero.
- `xg_90 = round(xg / 34.0, 2)` divides by static constant 34.0 (never zero).
- Returned metrics are bounded within $[0.0, 100.0]$ for `moneyball_index` and $\ge 0.0$ for xG/xA.

### C. Test Executions & Empirical Output
1. **Adversarial Stress Harness (`.agents/challenger_2/adversarial_auction_moneyball_stress.py`)**:
   ```
   Ran 20 tests in 0.071s
   OK
   ```
   * Budget edge cases: $C = S \implies \text{max bid} = 1$; bankruptcy ($C < S$) triggers warning; 1 slot left $\implies \text{max bid} = C$; 25/25 filled $\implies \text{max bid} = C$.
   * Full 25-man sequential draft simulation: invariant preserved across all 25 purchases.
   * Full parameter grid test (>2000 combinations) on `compute_moneyball_metrics`: 0 exceptions, 0 NaNs, 0 Infs.
   * Modificatore difesa simulation: exact thresholds tested (<6.00: 0, 6.00-6.49: +1, 6.50-6.99: +3, $\ge 7.00$: +6).

2. **Root Acceptance Tests**:
   - `python3 test_data_integrity.py`: 8/8 tests PASSED (exit code 0).
   - `python3 test_lineup_logic.py`: 7/7 tests PASSED (exit code 0).
   - `python3 -m unittest tests/test_auction_max_bid.py tests/test_moneyball.py tests/test_moneyball_metrics.py`: 28/28 tests PASSED.
   - `python3 -m unittest tests/test_tier1_feature_coverage.py tests/test_tier2_boundary_corner.py tests/test_tier3_combinations.py tests/test_tier4_real_world.py tests/test_lineup_optimizer.py`: 90/90 tests PASSED.

---

## 2. Logic Chain

1. **Step 1 — Mathematical Invariant of Auction Max Bid**:
   When user has $C$ credits and $S$ remaining slots, purchasing the current player leaves $S - 1$ slots to be filled. Under Fantacalcio rules, each slot requires at least 1 credit. The minimum reserve is thus $S - 1$ credits. The maximum available bid for the current player is:
   $$\text{MaxBid} = C - (S - 1)$$
   - If $C = S$, $\text{MaxBid} = S - (S - 1) = 1$.
   - If $S = 1$, $\text{MaxBid} = C - 0 = C$.
   - If $C < S$, $\text{MaxBid} \le 0$, and `Math.max(1, C - (S - 1))` combined with the evaluator's `currentBid > userMaxBid` check immediately issues an `ATTENZIONE BUDGET` warning.
   - For role-specific safety, $\text{otherRolesReserve} = S - 1$, preserving exact budget invariants across all 4 roles (3 P, 8 D, 8 C, 6 A).

2. **Step 2 — Opponent Ceiling & Winning Threshold**:
   - Opponents with $C_{opp}$ credits and $S_{opp}$ empty slots have maximum single bid $\text{Ceiling}_{opp} = \max(1, C_{opp} - (S_{opp} - 1))$.
   - The mathematical winning threshold $\text{WinningThreshold} = \text{TopRivalCeiling} + 1$ guarantees mathematical certainty of winning an auction if the user bids at or above this value.
   - When an opponent has 0 credits, their ceiling defaults safely to 1 cr.

3. **Step 3 — Moneyball Pipeline Resilience**:
   - `compute_moneyball_metrics` enforces `cost = max(1, prezzo_target)` and `max(2, cost)` for division terms.
   - Players with zero minutes, 0 goals, 0 assists, 0 FVM produce non-null, valid numeric baseline indices ($20.0 - 45.0$) rather than throwing ZeroDivisionError.
   - The 2,000+ adversarial parameter permutation grid demonstrated zero unhandled exceptions.

4. **Step 4 — Dataset Integrity & Backwards Compatibility**:
   - `data/players.json`, `data/players_db.json`, and `data/players.csv` each contain all 588 players.
   - All critical keys (`id`, `nome`, `squadra`, `squadra_code`, `ruolo`, `prezzo_target`, `prezzo_max`, `fvm_1000`, `xg`, `xa`, `xg_90`, `xa_90`, `moneyball_index`) are present and free of nulls or NaNs.
   - Full backwards compatibility is preserved with `test_data_integrity.py`.

---

## 3. Caveats

1. **Rival Spend Real-time Interaction**:
   The dashboard provides interactive `- Spesa` buttons for the 9 league rivals; in actual live auction usage, the user must click and enter spent amounts as rivals win auctions to keep rival ceilings up-to-date.
2. **Cross-Module Note**:
   In `tests/test_adversarial_lineup.py` (lineup optimizer edge cases), 3 test failures were noted (`test_only_three_fit_defenders_forces_3xx_formations`, `test_name_normalization_accents_and_special_chars`, `test_home_advantage_increases_expected_score`). These pertain to the lineup selection engine (reviewed by challenger_1) and do not affect the auction calculator or moneyball pipeline.

---

## 4. Conclusion

**Verdict**: **APPROVE**

The Auction Max Price Calculator formulas in `dashboard/index.html` and the Moneyball Index pipeline in `src/models.py`, `src/parsers/players_parser.py`, and `src/storage/` satisfy all mathematical invariants, edge cases, and integrity criteria. Division-by-zero is strictly prevented, role reserves are mathematically exact, and all datasets are 100% parseable and valid.

---

## 5. Verification Method

To independently reproduce and verify these findings:

```bash
# 1. Run Challenger 2's comprehensive adversarial test suite
python3 .agents/challenger_2/adversarial_auction_moneyball_stress.py

# 2. Run Root Data Integrity Acceptance Test
python3 test_data_integrity.py

# 3. Run Lineup Logic Acceptance Test
python3 test_lineup_logic.py

# 4. Run Auction & Moneyball Unit Tests
python3 -m unittest tests/test_auction_max_bid.py tests/test_moneyball.py tests/test_moneyball_metrics.py
```
