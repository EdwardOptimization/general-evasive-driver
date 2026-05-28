# M1174 V4 Public Base Action-Divergent Candidate Export Tooling

## Purpose

M1174 implements deterministic tooling for the action-divergent candidate
export designed in M1173.

This milestone is infrastructure only. It does not run relocation replay, run
mining, train actor weights, run PPO, promote, use private holdout, convert rows
into a proof corpus, or change actor inputs.

## Implementation

Added:

```text
src/autodrift/action_divergent_candidate_export.py
tests/test_action_divergent_candidate_export.py
```

The exporter:

1. reads an existing outcome CSV;
2. keeps `wrong_matched_history` rows only;
3. filters by:

```text
margin_gap >= 0.0025
and (
  first_action_distance >= 0.15
  or action_trajectory_distance_mean >= 0.06
)
```

4. computes:

```text
score =
  first_action_distance / 0.25
  + action_trajectory_distance_mean / 0.15
  + max(margin_gap, 0) / 0.01
  + 0.25 * target_z_delta
  - visible_distance / 0.25
```

5. selects rows by physical-pair round robin under source-balance quotas;
6. writes:

```text
candidate_pool.csv
candidate_outcomes.csv
rejected_candidates.csv
summary.json
```

## Verification

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_action_divergent_candidate_export.py
```

Result:

```text
3 passed
```

The tests cover filtering, deterministic score presence, source-balanced
selection, summary fields, and artifact writing.

## Guardrail

No relocation replay, mining, actor training, PPO, promotion, private holdout,
row conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: action_divergent_candidate_export_tooling_admit_real_export_run
next: m1175-v4-public-base-action-divergent-candidate-export-run
```
