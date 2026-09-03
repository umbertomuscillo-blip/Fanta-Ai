# DISPATCH Log

## 2026-09-02T12:29:47Z
You are the Project Orchestrator for the Fantacalcio 2026/2027 automated data pipeline project.

Working Directory: /Users/umbertomuscillo/Documents/Fantacalcio/.agents/orchestrator_1/
Workspace Directory: /Users/umbertomuscillo/Documents/Fantacalcio
Original Request: /Users/umbertomuscillo/Documents/Fantacalcio/.agents/ORIGINAL_REQUEST.md

User Objective & Requirements:
1. Pipeline di Aggiornamento Manuale: Main script (e.g. `update_fanta_data.py`) to update all data when run.
2. Ricerca e Selezione Fonti Autonoma: Autonomously research and select the best free sources (fantacalcio websites, sports outlets, APIs) to extract player stats, probable lineups, and calendar/fixtures.
3. Estrazione e Strutturazione dei Dati: Data must be cleaned and stored locally in `data/` (JSON / CSV).
4. Validazione Stagione 2026/2027: All data must strictly pertain to Serie A season 2026/2027 (including newly promoted teams like Como, Parma, Venezia; excluding relegated teams).
5. Acceptance Criteria:
   - Automated test suite (e.g. `test_data_integrity.py`) verifying file existence, team roster validity (e.g. Como, Parma present; old relegated teams absent), and exit code 0.
   - Independent Agent-as-Judge review verifying data consistency, realistic lineups, roles, and stats.

Please create your plan.md, progress.md, and BRIEFING.md in your working directory, decompose the task, dispatch specialist subagents, drive the project to completion, and report when finished.
