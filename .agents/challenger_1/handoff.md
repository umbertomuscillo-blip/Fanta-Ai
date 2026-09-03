# Handoff Report: Adversarial Stress-Testing of Algoritmo "Chi Schiero"

**Agent**: challenger_1 (Empirical Challenger)  
**Milestone**: Adversarial Verification & Hardening (M2)  
**Verdict**: **REQUEST_CHANGES**  
**Date**: 2026-09-02T13:41:00Z  

---

## 1. Observation

Adversarial evaluation of `best_lineup.py` and `src/best_lineup.py` across 24 aggressive empirical stress tests revealed both high core competence and 4 concrete failure modes / vulnerabilities:

### A. Core Properties Verified (PASS)
- **Official 7 Formations Evaluation**: All 7 modulos (`3-4-3`, `3-5-2`, `4-3-3`, `4-4-2`, `4-5-1`, `5-3-2`, `5-4-1`) evaluate strictly with 11 starters satisfying exact role counts (`tests/test_adversarial_lineup.py:TestDepletedRostersAndFormationInvariants`).
- **Modificatore Difesa Mathematical Boundaries**: Exact boundary tests confirmed:
  - Average `5.999` $\to$ `0.0` bonus; Average `6.000` $\to$ `+1.0` bonus (`test_boundary_5_999_vs_6_000`).
  - Average `6.499` $\to$ `+1.0` bonus; Average `6.500` $\to$ `+3.0` bonus (`test_boundary_6_499_vs_6_500`).
  - Average `6.999` $\to$ `+3.0` bonus; Average `7.000` $\to$ `+6.0` bonus (`test_boundary_6_999_vs_7_000`).
  - 5-defender lineup: Only top 3 defenders + GK are averaged; D4 and D5 low ratings do not degrade the modifier average (`test_modifier_only_uses_top_three_defenders_when_five_defenders_fielded`).
  - 3-defender formation: Modifier bonus is strictly `0.0` regardless of average ratings (`test_three_defender_formation_never_yields_modifier_bonus`).
  - Flag `--no-modificatore` / `use_modifier=False` strictly sets bonus to `0.0` (`test_use_modifier_false_completely_disables_modifier_bonus`).
- **Injuries & Suspensions Exclusion**: Injured/suspended players with extreme synthetic stats (e.g. MV=10.0, xG=50.0) are strictly excluded from both starting 11 and bench (`test_injured_superstar_with_astronomical_stats_is_never_fielded`).
- **Bench Structure**: Bench contains up to 12 players ordered by role partition `[P, ..., D, ..., C, ..., A]` and sorted by descending priority within each role (`test_bench_role_partition_and_priority_invariants`).

---

### B. Identified Vulnerabilities & Failure Modes

#### 1. BUG-ADV-01: False-Positive Team Code Matching on Empty Strings Reverses Home/Away Context
- **Location**: `src/best_lineup.py`, lines 336 and 343:
  ```python
  if p_team.lower() == h_team.lower() or p_team_code.upper() == fix.get("home_team_code", "").upper():
      is_home = True
  ```
- **Observed Behavior**: When `p_team_code` is empty `""` (e.g., custom user roster dictionary without `squadra_code`) and a fixture object has empty `home_team_code: ""` or lacks the key, `"" == ""` evaluates to `True`.
- **Impact**: Any away team player is misclassified as playing at home (`is_home = True`), causing inaccurate fixture difficulty ratings, artificial home MV bonuses (+0.25 pt), and inverted opponent assignment.
- **Empirical Test**: `test_reproduce_bug_adv_01_empty_team_code_home_away_reversal` in `tests/test_adversarial_lineup.py`.

#### 2. BUG-ADV-02: Cross-Club Name Collisions and Unchecked Substring Matching in Lineup Scanner
- **Location**: `src/best_lineup.py`, lines 363-424:
  ```python
  for ml in matches_lineups:
      for t_lineup in [ml.get("home_lineup"), ml.get("away_lineup")]:
          ...
          for tit in t_lineup.get("titolari", []):
              tit_name = tit.get("nome", "")
              if normalize_name(tit_name) == p_norm or p_norm in normalize_name(tit_name) or normalize_name(tit_name) in p_norm:
                  status = "STARTER"
                  probability = tit.get("probabilita", 90)
                  if p_role == "C" and tit.get("ruolo") in {"P", "D", "C", "A"}:
                      p_role = tit.get("ruolo")
                  break
  ```
- **Observed Behavior**: The lineup scanner iterates over all 20 clubs without checking if `t_lineup.get("squadra")` matches the player's team. Unanchored substring check `p_norm in normalize_name(tit_name)` causes short names to match unrelated players across different teams:
  - Dennis Man (Parma midfielder, role `C`) matches Roma's defender Mancini (`"mancini"` contains `"man"`) or Monza's defender Mangas (`"mangas"` contains `"man"`).
  - Line 397 overwrites Man's role from `C` to `D`.
- **Impact**: Player roles are silently corrupted, causing the optimizer to evaluate invalid rosters (e.g. claiming 4 defenders are available when only 3 were in the squad).
- **Empirical Test**: `test_reproduce_bug_adv_02_greedy_cross_club_role_overwrite` in `tests/test_adversarial_lineup.py`.

#### 3. BUG-ADV-03: Fallback ID Collision (`id: 9999`) Drops Unlisted Bench Candidates
- **Location**: `src/best_lineup.py`, line 190 and lines 670-671:
  ```python
  # line 190:
  return {"id": 9999, "nome": name, ...}
  # line 670:
  starters_ids = {s.id for s in best_starters}
  bench_candidates = [ctx for ctx in contexts if ctx.id not in starters_ids and ctx not in excluded_players]
  ```
- **Observed Behavior**: All unlisted/custom players parsed through `match_player` receive a static `id: 9999`. If one unlisted player is selected as a starter, `starters_ids` contains `9999`. Line 671 then filters out ALL other unlisted players from the bench candidate pool because `ctx.id not in starters_ids` fails.
- **Impact**: Unlisted substitutes vanish from the bench.
- **Empirical Test**: `test_reproduce_bug_adv_03_fallback_id_collision_drops_bench_players` in `tests/test_adversarial_lineup.py`.

#### 4. BUG-ADV-04: Missing Unicode Diacritic/Accent Stripping in `normalize_name`
- **Location**: `src/best_lineup.py`, lines 95-100:
  ```python
  def normalize_name(name: str) -> str:
      s = str(name).strip().lower()
      s = re.sub(r'[\.\,\'\"\-\_]', ' ', s)
      s = re.sub(r'\s+', ' ', s).strip()
      return s
  ```
- **Observed Behavior**: Special characters such as `Ç`, `ğ`, `é`, `á`, `ñ` are not normalized to ASCII equivalents (e.g., `"Hakan Çalhanoğlu"` $\to$ `"hakan çalhanoğlu"` instead of `"hakan calhanoglu"`).
- **Impact**: Roster lookups with accented characters fail to match unaccented names in datasets, falling back to dummy records.
- **Empirical Test**: `test_reproduce_bug_adv_04_missing_unicode_diacritics_normalization` in `tests/test_adversarial_lineup.py`.

---

## 2. Logic Chain

1. **Premise 1**: The Algoritmo "Chi Schiero" is designed to reliably choose the optimal starting 11, bench, and formation given any user roster and matchday conditions.
2. **Premise 2**: Reliable tactical choices require invariant role preservation, accurate home/away context, and non-colliding entity tracking.
3. **Step 1 (BUG-ADV-01)**: `p_team_code.upper() == fix.get("home_team_code", "").upper()` is truthy when both strings are `""`. A defender playing away without an explicit team code is evaluated as playing at home, receiving an improper +0.25 MV adjustment and distorted opponent difficulty.
4. **Step 2 (BUG-ADV-02)**: Substring matching without club anchoring alters player roles across clubs. When a midfielder is reclassified as a defender, 3-defender rosters can illegitimately trigger 4-defender formations.
5. **Step 3 (BUG-ADV-03)**: Generating `id: 9999` for all fallback players breaks set uniqueness in bench candidate selection (`ctx.id not in starters_ids`), dropping bench players.
6. **Step 4 (BUG-ADV-04)**: Punctuation-only regex misses diacritic normalization, reducing match hit rate for international players.
7. **Conclusion**: While the core mathematical formulation of Modificatore Difesa and formation evaluation is sound, the 4 identified bugs constitute concrete vulnerabilities that must be addressed.

---

## 3. Caveats

- **External Data Consistency**: The test suite evaluated the optimizer against `data/probabili_formazioni.json` and `data/calendario_serie_a.json`. Synthetic or heavily modified datasets outside standard schema were tested via explicit mock harnesses.
- **Mantra Multi-Role Positioning**: The optimizer optimizes for standard Classic Fantacalcio roles (`P`, `D`, `C`, `A`). Mantra multi-role tactical graph optimization was not within the primary scope of `best_lineup.py`.

---

## 4. Conclusion

**Verdict**: **REQUEST_CHANGES**

The core lineup algorithm is mathematically sound and adheres to Fantacalcio Modificatore rules and formation definitions. However, the 4 identified vulnerabilities (BUG-ADV-01 through BUG-ADV-04) require targeted fixes:
1. **Fix BUG-ADV-01**: Guard team code comparison: `if p_team_code and (p_team_code.upper() == fix.get("home_team_code", "").upper()): ...`
2. **Fix BUG-ADV-02**: Anchor lineup lookup to the player's team (`t_lineup.get("squadra") == p_team`) or require exact token / word-boundary matches before altering `p_role`.
3. **Fix BUG-ADV-03**: Use unique IDs for unlisted players (e.g., `id: 90000 + hash(name) % 10000`) or filter bench candidates by player instance/name.
4. **Fix BUG-ADV-04**: Add `unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')` to `normalize_name`.

---

## 5. Verification Method

To independently execute and verify the adversarial stress test suite and bug reproduction oracles:

```bash
# 1. Run full adversarial stress test suite (24 tests)
python3 -m unittest tests/test_adversarial_lineup.py -v

# 2. Run existing lineup logic tests (7 tests)
python3 test_lineup_logic.py

# 3. Run full project test discovery (142 tests)
python3 -m unittest discover -s tests -v

# 4. Verify CLI execution in JSON mode
python3 best_lineup.py --roster "Svilar, Dimarco, Bremer, Bastoni, Calhanoglu, Pulisic, Zaccagni, Nico Paz, Retegui, Malen, Martinez L." --giornata 1 --modificatore --json
```
