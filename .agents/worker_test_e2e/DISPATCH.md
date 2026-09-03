## 2026-09-02T12:35:00Z
You are the E2E Test Architect for the Fantacalcio 2026/2027 automated data pipeline project.

Working directory: /Users/umbertomuscillo/Documents/Fantacalcio/.agents/worker_test_e2e/
Workspace root: /Users/umbertomuscillo/Documents/Fantacalcio
Original Request: /Users/umbertomuscillo/Documents/Fantacalcio/.agents/ORIGINAL_REQUEST.md
Project Plan: /Users/umbertomuscillo/Documents/Fantacalcio/PROJECT.md
Spec Miner Report: /Users/umbertomuscillo/Documents/Fantacalcio/.agents/survey_spec_miner/spec_report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All test implementations must be genuine, comprehensive, and opaque-box. DO NOT write dummy tests or bypass verification.

Your write ownership:
- You exclusively own `test_data_integrity.py`, `TEST_INFRA.md`, `TEST_READY.md`, and any test runner or test suite files under `tests/`.
- DO NOT modify implementation files in `src/` or `update_fanta_data.py`.

Your mission (E2E Testing Track):
1. Read ORIGINAL_REQUEST.md, PROJECT.md, and survey_spec_miner/spec_report.md.
2. Create `TEST_INFRA.md` at project root documenting test architecture, methodology, and feature coverage mapping.
3. Implement the primary acceptance test suite:
   `test_data_integrity.py` at workspace root.
   - Must use Python standard library `unittest`.
   - Must verify:
     1. File existence for all expected output files in `data/` (JSON and CSV for players, lineups, calendar, teams, sync_report, and players_db.json).
     2. Strict 2026/2027 team roster validation (20 exact teams; Como, Parma, Venezia must be present; Salernitana, Sassuolo, Frosinone must be strictly absent).
     3. Player dataset validation (>500 records, correct role distribution P/D/C/A, valid quotazioni > 0, price scaling).
     4. Lineup dataset validation (10 match fixtures, 20 teams, each team having exactly 11 starters, bench, ballotaggi structure).
     5. Calendar dataset validation (38 matchdays, 380 total matches, valid dates/teams).
     6. Pipeline execution test (running `python3 update_fanta_data.py` exits with code 0).
4. Implement comprehensive 4-Tier test cases under `tests/`:
   - Tier 1: Feature Coverage (≥5 tests per feature).
   - Tier 2: Boundary & Corner Cases (empty cache, malformed inputs, single-flag runs, missing files, corrupted records).
   - Tier 3: Cross-Feature Combinations (pairwise CLI combinations, lineup & player cross-reference consistency, calendar & lineup sync).
   - Tier 4: Real-World Application Scenarios (auction strategy dataset consumption, matchday lineup evaluation, fantasy league roster export).
5. Run the test suite using `python3 -m unittest discover tests` and `python3 test_data_integrity.py`.
6. Publish `TEST_READY.md` at project root summarizing the test suite, test commands, coverage breakdown, and passing status.
7. Record your report in `/Users/umbertomuscillo/Documents/Fantacalcio/.agents/worker_test_e2e/report.md` and write `handoff.md`.
8. Send a message to orchestrator when finished.

## 2026-09-02T13:29:52Z
You are worker_test_e2e.
Your mission: Create and execute the comprehensive automated test suite for the Fantacalcio 2026/2027 Advanced Suite in /Users/umbertomuscillo/Documents/Fantacalcio:

1. **`test_lineup_logic.py` (Root Acceptance Test Suite)**:
   - Verifies all acceptance criteria from /Users/umbertomuscillo/Documents/Fantacalcio/ORIGINAL_REQUEST.md:
     * Valid formations generated (3-4-3, 3-5-2, 4-3-3, 4-4-2, 4-5-1, 5-3-2, 5-4-1).
     * Strict exclusion of injured/suspended players (never schierati).
     * Exact Modificatore Difesa calculation (thresholds 6.00 -> +1, 6.50 -> +3, 7.00 -> +6, only when $\ge 4$ defenders start).
     * Preservation of JSON dataset structure (`players.json`, `players_db.json`) containing new `xg`, `xa`, `moneyball_index` fields without corruption.
     * Exit code 0 on all tests.

2. **Modular E2E Test Suite in `tests/`**:
   - `tests/test_lineup_optimizer.py`: 4 tiers of tests:
     * Tier 1: Feature coverage across all 7 formations, starter/bench selection, modifier scoring, goalkeeper pairing difficulty.
     * Tier 2: Boundary & Corner cases (all-defender squad, all-forward squad, border average ratings 5.99 vs 6.00 vs 6.49 vs 6.50 vs 6.99 vs 7.00, heavily injured squad).
     * Tier 3: Pairwise combinations (defense modifier + high xG forwards vs 3-4-3 attack setup; goalkeeper grid difficulty + home/away bonus).
     * Tier 4: Real-world application scenarios (5 realistic fantasy squad archetypes: Balanced Meta, Modificatore Specialist, All-Out Attack, Budget Wonderkids, Injury Emergency Squad).
   - `tests/test_moneyball_metrics.py`: Schema validation, non-empty xG/xA, positive Moneyball Index, backwards compatibility.
   - `tests/test_auction_max_bid.py`: Mathematical verification of user max bid, rival ceiling, winning bid threshold, and role reserve formulas.

3. **Coordination**:
   - Run the test suite: `python3 test_lineup_logic.py`, `python3 test_data_integrity.py`, and `python3 -m unittest discover tests`.
   - Create `TEST_READY.md` summarizing the test suites, runner commands, test counts per tier, and coverage breakdown.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work.

Working directory: /Users/umbertomuscillo/Documents/Fantacalcio/.agents/worker_test_e2e
Write `test_results.md` and `handoff.md`, then send a message to parent when done.
