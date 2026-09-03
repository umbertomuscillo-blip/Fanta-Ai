# Test Results — Fantacalcio 2026/2027 Advanced Suite

**Date & Time (UTC):** 2026-09-02T13:38:30Z  
**Agent:** `worker_test_e2e`  
**Execution Environment:** macOS (Darwin 24.6.0, Python 3.9.6)  
**Total Test Count:** 133 automated tests  
**Overall Verdict:** **100% PASS (0 Failures, 0 Errors, 0 Regressions)**  

---

## 1. Primary Acceptance Test Suites Execution

### 1.1 `test_lineup_logic.py` (Lineup Optimizer & Acceptance Criteria)
- **Command:** `python3 test_lineup_logic.py -v`
- **Result:** `Ran 7 tests in 0.419s — OK`
- **Detailed Test Breakdown:**
  1. `test_all_seven_formations_are_evaluated`: PASS
  2. `test_formation_role_distribution_invariants`: PASS
  3. `test_strict_exclusion_of_injured_and_suspended_players`: PASS
  4. `test_modificatore_thresholds`: PASS (Verifies 6.00 -> +1, 6.50 -> +3, 7.00 -> +6)
  5. `test_modificatore_not_applied_for_3_defenders`: PASS (Verifies +0 for 3-4-3 / 3-5-2)
  6. `test_cli_default_execution`: PASS (Executes `best_lineup.py` CLI)
  7. `test_cli_execution_with_string_roster`: PASS

### 1.2 `test_data_integrity.py` (Data Pipeline Integrity Acceptance)
- **Command:** `python3 test_data_integrity.py -v`
- **Result:** `Ran 8 tests in 1.720s — OK`
- **Detailed Test Breakdown:**
  1. `test_pipeline_execution_exit_code_zero`: PASS (`update_fanta_data.py --all` exit code 0)
  2. `test_all_expected_files_exist_and_non_empty`: PASS (All 10 data artifacts verified)
  3. `test_teams_json_exact_20_clubs`: PASS (Como, Parma, Venezia in; Relegated out)
  4. `test_teams_csv_exact_20_clubs`: PASS
  5. `test_players_json_count_and_roles`: PASS (>500 players, P/D/C/A quotas, valid prices)
  6. `test_players_db_compatibility_structure`: PASS
  7. `test_lineups_10_matches_and_20_teams`: PASS (10 fixtures, 20 clubs, 11 starters each)
  8. `test_calendar_38_giornate_and_380_matches`: PASS (38 giornate, 380 matches)

---

## 2. Modular E2E Test Suite Execution (`tests/`)

- **Command:** `python3 -m unittest discover tests -v`
- **Result:** `Ran 118 tests in 7.442s — OK`

### 2.1 `tests/test_lineup_optimizer.py` (11 tests)
- `test_t1_01_feature_all_seven_formations_structure`: PASS
- `test_t1_02_starter_and_bench_selection_integrity`: PASS
- `test_t1_03_goalkeeper_match_context`: PASS
- `test_t2_01_modifier_border_5_99_vs_6_00`: PASS
- `test_t2_02_modifier_border_6_49_vs_6_50`: PASS
- `test_t2_03_modifier_border_6_99_vs_7_00`: PASS
- `test_t2_04_heavily_injured_squad_graceful_handling`: PASS
- `test_t3_01_modifier_triggers_only_on_four_defenders`: PASS
- `test_t4_01_archetype_balanced_meta`: PASS
- `test_t4_02_archetype_modificatore_specialist`: PASS
- `test_t4_03_archetype_injury_emergency`: PASS

### 2.2 `tests/test_moneyball_metrics.py` (11 tests)
- `test_players_json_schema_has_moneyball_fields`: PASS
- `test_players_csv_schema_has_moneyball_columns`: PASS
- `test_players_db_json_role_partitions_have_moneyball_fields`: PASS
- `test_outfield_players_have_positive_expected_goals_or_assists`: PASS
- `test_moneyball_index_is_strictly_positive_and_bounded`: PASS
- `test_top_stars_moneyball_indexes`: PASS
- `test_goalkeeper_moneyball_metrics`: PASS
- `test_defender_moneyball_metrics_with_modifier`: PASS
- `test_midfielder_moneyball_penalty_taker`: PASS
- `test_forward_top_striker_metrics`: PASS
- `test_legacy_fields_are_fully_preserved`: PASS

### 2.3 `tests/test_auction_max_bid.py` (10 tests)
- `test_initial_auction_state_max_bid`: PASS (500 cr, 25 slots -> 476 max bid)
- `test_single_slot_remaining_max_bid`: PASS (1 slot left -> 100% budget)
- `test_intermediate_auction_scenarios`: PASS
- `test_edge_case_minimum_credits_per_slot`: PASS (25 cr, 25 slots -> 1 cr)
- `test_edge_case_zero_slots_or_exhausted_credits`: PASS
- `test_rival_spending_ceilings`: PASS
- `test_winning_bid_threshold_user_leading`: PASS
- `test_role_reserves_unfilled_roster`: PASS (25 cr reserve for 25 empty slots)
- `test_role_reserves_partially_filled_roster`: PASS
- `test_dashboard_html_contains_max_bid_formulas`: PASS

### 2.4 Pipeline Feature & Integration Suites (86 tests)
- `tests/test_tier1_feature_coverage.py`: 48 tests — PASS
- `tests/test_tier2_boundary_corner.py`: 12 tests — PASS
- `tests/test_tier3_combinations.py`: 12 tests — PASS
- `tests/test_tier4_real_world.py`: 7 tests — PASS
- `tests/test_moneyball.py`: 7 tests — PASS

---

## 3. Summary Scorecard

| Test Suite File | Test Count | Pass | Fail | Error |
|---|---|---|---|---|
| `test_lineup_logic.py` | 7 | 7 | 0 | 0 |
| `test_data_integrity.py` | 8 | 8 | 0 | 0 |
| `tests/test_lineup_optimizer.py` | 11 | 11 | 0 | 0 |
| `tests/test_moneyball_metrics.py` | 11 | 11 | 0 | 0 |
| `tests/test_auction_max_bid.py` | 10 | 10 | 0 | 0 |
| `tests/test_tier1_feature_coverage.py` | 48 | 48 | 0 | 0 |
| `tests/test_tier2_boundary_corner.py` | 12 | 12 | 0 | 0 |
| `tests/test_tier3_combinations.py` | 12 | 12 | 0 | 0 |
| `tests/test_tier4_real_world.py` | 7 | 7 | 0 | 0 |
| `tests/test_moneyball.py` | 7 | 7 | 0 | 0 |
| **TOTAL** | **133** | **133** | **0** | **0** |
