# M1175 V4 Public Base Action-Divergent Candidate Export Run

## Purpose

M1175 runs the deterministic exporter implemented in M1174 on the M1161
outcome artifact.

This milestone is an export-only infrastructure step. It does not run
relocation replay, run mining, train actor weights, run PPO, promote, use
private holdout, convert rows into a proof corpus, or change actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.action_divergent_candidate_export \
  --outcome-csv runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv \
  --run-dir runs/m1175_action_divergent_candidate_export \
  --max-candidates 240 \
  --max-candidates-per-physical-pair 20 \
  --max-candidates-per-checkpoint-target 80 \
  --target-min-physical-pairs 12 \
  --target-min-left-steps 6 \
  --target-min-targets 3 \
  --max-rows-per-pair-fraction 0.15
```

Result:

```text
decision=action_divergent_candidates_ready
passed=True
```

## Artifacts

```text
runs/m1175_action_divergent_candidate_export/summary.json
runs/m1175_action_divergent_candidate_export/candidate_pool.csv
runs/m1175_action_divergent_candidate_export/candidate_outcomes.csv
runs/m1175_action_divergent_candidate_export/rejected_candidates.csv
```

## Export Summary

```text
input_rows: 27510
wrong_history_rows: 4585
candidate_pool_rows: 343
selected_rows: 240
selected_physical_pairs: 17
selected_left_steps: 9
selected_targets: 3
selected_checkpoints: 6
max_selected_rows_per_physical_pair: 15
max_selected_pair_fraction: 0.0625
```

The export passes the M1173 diversity gates:

```text
selected_physical_pairs >= 12
selected_left_steps >= 6
selected_targets >= 3
selected_checkpoints >= 6
max_selected_pair_fraction <= 0.15
```

## Action-Divergence Statistics

Selected rows:

```text
success_drop_rows: 0
normal_better_rows: 30
margin_gap_mean: 0.0089004993
margin_gap_p90: 0.0201612121
first_action_distance_mean: 0.1887425895
first_action_distance_p90: 0.2802288532
action_trajectory_distance_mean: 0.1441020185
action_trajectory_distance_p90: 0.2938849628
```

This is not a proof corpus. It is a source-diverse, action-divergent candidate
set for a later bounded relocation replay. The export intentionally admits
rows where wrong-history rollout still succeeds in the original M1161 outcome
geometry.

## Caveat

`source_obstacle_bucket` is `x=nan|y=nan` for all selected rows because the
M1161 outcome artifact does not include obstacle geometry columns that the
source-balance helper can bucket. The M1175 diversity claim is therefore scoped
to physical pairs, checkpoints, targets, and left steps, not explicit obstacle
geometry buckets.

## Guardrail

No relocation replay, mining, actor training, PPO, promotion, private holdout,
row conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: action_divergent_candidates_ready_route_to_bounded_relocation_design
next: m1176-v4-public-base-action-divergent-bounded-relocation-design
```
