# Plan — Fantacalcio 2026/2027 Automated Data Pipeline

## Objective
Build a complete automated data pipeline for Fantacalcio 2026/2027 that fetches, cleans, structures, and stores Serie A data (players, stats, quotazioni, probable lineups, fixtures/calendar) locally in `data/` (JSON/CSV) when executed via `python update_fanta_data.py`. Fully verify with automated tests (`test_data_integrity.py`), E2E test tiers, Agent-as-Judge review, and Forensic Audit.

## Phases
1. **Phase 0: Survey & Discovery**
   - Survey available web/API sources for Serie A & Fantacalcio data (lineups, stats, fixtures).
   - Inspect existing workspace layout (`src/`, `data/`, `dashboard/`).
   - Mine exact schema specifications and data requirements for Serie A 2026/2027.
2. **Phase 1: Architecture & Decomposition (PROJECT.md)**
   - Define architecture, module interfaces, code layout, and feature inventory.
   - Decompose into Milestones (Data Ingestion/Scraping, Data Processing/Cleaning & Export, Main Pipeline Runner `update_fanta_data.py`, E2E Test Suite `test_data_integrity.py`).
3. **Phase 2: Dual Track Execution**
   - **Track A (E2E Testing Track)**: Build test infra and 4 tiers of test cases (Feature, Boundary, Combinations, Real-World Application) -> produce `TEST_READY.md`.
   - **Track B (Implementation Track)**: Implement scrapers, data models, processors, storage, and CLI runner.
4. **Phase 3: Integration & Final Verification**
   - Execute test suite (`test_data_integrity.py` + full E2E tiers).
   - Adversarial coverage hardening (Tier 5).
   - Independent Agent-as-Judge review on data coherence.
   - Forensic Integrity Audit (`teamwork_preview_auditor`).
   - Final report and user delivery.
