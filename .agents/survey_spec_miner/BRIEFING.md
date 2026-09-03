# BRIEFING — 2026-09-02T15:29:30Z

## Mission
Mine, analyze, and formalize the detailed mathematical and domain specifications for R1 (Auction Max Price Calculator), R2 (Lineup Optimizer best_lineup.py), and R3 (Moneyball Index).

## 🔒 My Identity
- Archetype: SPECIFICATION MINER
- Roles: survey_spec_miner
- Working directory: /Users/umbertomuscillo/Documents/Fantacalcio/.agents/survey_spec_miner
- Original parent: f4d55cf5-9438-4d7b-af1f-ef5251514222
- Milestone: Survey & Specification

## 🔒 Key Constraints
- Discover and document features by probing authoritative sources
- Read-only on codebase implementation; no production code changes
- Provide rigorous mathematical formulations and domain logic
- Output reports to analysis.md and handoff.md in working directory
- Communicate completion to parent via send_message

## Current Parent
- Conversation ID: f4d55cf5-9438-4d7b-af1f-ef5251514222
- Updated: 2026-09-02T15:29:30Z

## Task Summary
- **What to build**: Specification Report for Auction Max Price Calculator, Lineup Optimizer, and Moneyball Index
- **Success criteria**: Detailed, unambiguous mathematical formulas, edge cases, Fantacalcio domain rules, and data structures
- **Interface contracts**: ORIGINAL_REQUEST.md, PROJECT.md
- **Code layout**: .agents/survey_spec_miner/analysis.md, handoff.md, progress.md

## Key Decisions Made
- Fully probed all authoritative sources (ORIGINAL_REQUEST.md, dashboard/index.html, goalkeeper_analyzer.py, models.py, lineups_parser.py, players.json).
- Formalized exact formulas:
  - R1: Strict Max Price $P_{strict\_max} = B - S + 1$, Guaranteed Price $M_{opp\_max} + 1$, and dynamic strategic price.
  - R2: 7 tactical formations (3-4-3..5-4-1), titolarità weighting, injury/suspension exclusion, goalkeeper fixture grid, and Defense Modifier (+1 at 6.0, +3 at 6.5, +6 at 7.0 for $\ge 4$ defenders).
  - R3: xG/xA normalization, $xFM$, $VORP$, $MVI = rac{VORP \cdot 100}{\max(1, 	ext{Price})}$, and undervalued gem detection rules.
- Created analysis.md and handoff.md with complete tables.

## Artifact Index
- /Users/umbertomuscillo/Documents/Fantacalcio/.agents/survey_spec_miner/analysis.md — Detailed Specification Report
- /Users/umbertomuscillo/Documents/Fantacalcio/.agents/survey_spec_miner/handoff.md — 5-Component Handoff Report
- /Users/umbertomuscillo/Documents/Fantacalcio/.agents/survey_spec_miner/progress.md — Liveness & progress tracking
