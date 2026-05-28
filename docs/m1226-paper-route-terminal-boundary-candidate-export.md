# M1226 Paper-Route Terminal-Boundary Candidate Export

## Summary

M1226 implements and runs the terminal-boundary candidate export adapter selected
by M1225.

Decision:

```text
terminal_boundary_candidate_export_passed
```

No relocation replay, source mining, outcome intervention, training, PPO,
checkpoint repair, promotion, private holdout, profile tuning, actor-input
change, or self-identification claim occurs in M1226.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.terminal_boundary_candidate_export \
  --candidate-scores runs/m1222_current_family_normal_success_boundary_source_smoke/candidate_scores.csv \
  --checkpoint-label l3_s111602 \
  --run-dir runs/m1226_terminal_boundary_candidate_export
```

## Artifacts

```text
runs/m1226_terminal_boundary_candidate_export/summary.json
runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv
runs/m1226_terminal_boundary_candidate_export/candidate_pool.csv
runs/m1226_terminal_boundary_candidate_export/rejected_candidates.csv
```

The adapter writes relocation-compatible fields, including:

```text
checkpoint_label
variant
left_seed / left_step
right_seed / right_step
target
normal_success
variant_success
success_drop
normal_margin
variant_margin
margin_gap
first_action_distance
action_trajectory_distance_mean / max
source_obstacle_body_x / y
source_obstacle_distance
source_obstacle_lateral_offset
physical_pair_key
source_obstacle_bucket
```

## Result

The export passed the pre-registered source-diversity gate:

```text
input rows:                         7200
wrong_matched_history rows:         7200
candidate_pool_rows:                 274
rejected_rows:                      6926
selected_physical_pairs:             110
selected_left_seeds:                   7
selected_right_seeds:                 24
selected_left_steps:                   5
selected_targets:                      2
selected_source_obstacle_buckets:      5
max_rows_per_physical_pair:            3
max_rows_per_physical_pair_fraction:   0.0109489051
max_left_seed_share:                   0.3649635036
max_target_share:                      0.6423357664
```

Pre-registered gate:

```text
selected_rows >= 120                         pass: 274
selected_physical_pairs >= 40                pass: 110
selected_left_seeds >= 6                     pass: 7
selected_right_seeds >= 15                   pass: 24
selected_left_steps >= 4                     pass: 5
selected_targets >= 2                        pass: 2
selected_source_obstacle_buckets >= 4        pass: 5
max_rows_per_physical_pair_fraction <= 0.05  pass: 0.0109489051
max_left_seed_share <= 0.40                  pass: 0.3649635036
max_target_share <= 0.70                     pass: 0.6423357664
```

The exported rows remain action-divergent candidates, not proof rows. M1222
already showed these rows do not yet have margin-threshold or success-drop
evidence under the unrelocated source geometry.

## Interpretation

M1226 resolves the schema/source-budget blocker from M1225:

```text
M1222 candidate_scores.csv
  -> M1226 relocation-compatible candidate_outcomes.csv
  -> later bounded terminal-boundary relocation replay
```

This is infrastructure evidence only. It supports running a bounded
terminal-boundary materialization test next, but it does not support a
recurrent-belief, history-necessity, self-identification, promotion, or
paper-level performance claim.

## Guardrails

Verified from the summary:

```text
relocation_replay_started: false
replay_started: false
source_mining_started: false
outcome_intervention_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
labels_enter_actor_input: false
self_identification_claimed: false
```

## Next

M1227 should run a bounded terminal-boundary relocation smoke using:

```text
checkpoint-policy:
  l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt

env config:
  configs/paper_route_corrected_profiles/m1207_l3_online_gru.json

outcome csv:
  runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv
```

M1227 may only claim materialized terminal-boundary evidence if the relocation
run produces source-diverse wrong-history rows with margin or success
degradation. If it fails, the route should fall back to stronger geometry/fault
source distributions rather than training or threshold weakening.
