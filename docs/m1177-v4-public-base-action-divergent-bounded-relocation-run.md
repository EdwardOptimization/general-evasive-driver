# M1177 V4 Public Base Action-Divergent Bounded Relocation Run

## Purpose

M1177 runs the bounded relocation replay designed in M1176 over the M1175
action-divergent candidate set.

This milestone runs relocation replay only. It does not run broad mining, train
actor weights, run PPO, promote, use private holdout, convert rows into a proof
corpus, or change actor inputs.

## Command

The command was the pre-registered M1176/M1177 command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy row15_current=runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --checkpoint-policy row15_previous_alpha015=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy previous_m1078_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --outcome-csv runs/m1175_action_divergent_candidate_export/candidate_outcomes.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-candidates 240 \
  --max-candidates-per-physical-pair 15 \
  --max-candidates-per-checkpoint-target 80 \
  --max-accepted-rows-per-physical-pair 20 \
  --target-min-physical-pairs 12 \
  --target-min-left-steps 6 \
  --target-min-targets 3 \
  --max-rows-per-pair-fraction 0.15 \
  --min-eligible-physical-pairs 12 \
  --max-candidate-pair-fraction 0.15 \
  --source-obstacle-distance-bucket-width 5.0 \
  --source-obstacle-lateral-bucket-width 1.0 \
  --target-normal-margins 0.00025,0.0005,0.00075,0.001,0.00125,0.0015,0.002,0.0025,0.003,0.004,0.005 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=0.0 \
  --body-lateral-offsets=0.0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --report-variants wrong_matched_history \
  --margin-bucket-width 0.005 \
  --control-checkpoint-label none \
  --device cpu \
  --run-dir runs/m1177_action_divergent_bounded_relocation_seed117700
```

## Artifacts

```text
runs/m1177_action_divergent_bounded_relocation_seed117700/summary.json
runs/m1177_action_divergent_bounded_relocation_seed117700/boundary_relocation_rows.csv
runs/m1177_action_divergent_bounded_relocation_seed117700/balanced_accepted_wrong_history_rows.csv
runs/m1177_action_divergent_bounded_relocation_seed117700/robustness_gates.csv
runs/m1177_action_divergent_bounded_relocation_seed117700/surface_summary.csv
```

## Result

```text
decision: reject_duplicate_dominated_boundary_surface
passed: false
```

Source budget and selection passed:

```text
candidate_rows: 240
selected_rows: 240
selected_physical_pairs: 17
selected_left_steps: 9
selected_targets: 3
selected_checkpoints: 6
max_selected_pair_fraction: 0.0625
source_budget_ready: true
relocation_replay_started: true
```

Relocation produced:

```text
raw_rows: 1054
raw_accepted_wrong_rows: 78
raw_accepted_wrong_physical_pairs: 2
raw_accepted_wrong_candidate_ids: 23
raw_accepted_wrong_source_pair_ids: 18
balanced_exportable_rows: 38
accepted_wrong_rows: 38
accepted_wrong_physical_pairs: 2
accepted_wrong_left_steps: 2
accepted_wrong_checkpoints: 5
accepted_wrong_targets: 1
accepted_wrong_normal_margin_buckets: 1
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.5263157895
control_accepted_wrong_rows: 0
```

Accepted physical-pair keys:

```text
116117:39:116124:15
116117:36:116124:15
```

Accepted target:

```text
future_yaw_response
```

Accepted margin range:

```text
accepted_wrong_normal_margin_min: 0.0017076332
accepted_wrong_normal_margin_max: 0.0024664053
accepted_wrong_margin_gap_mean: 0.0024798670
accepted_wrong_margin_gap_max: 0.0025323423
```

## Gate Failures

```text
accepted_wrong_rows: 38 < 80
accepted_wrong_physical_pairs: 2 < 10
accepted_wrong_left_steps: 2 < 5
accepted_wrong_targets: 1 < 2
accepted_wrong_normal_margin_buckets: 1 < 2
max_rows_per_physical_pair_fraction: 0.5263157895 > 0.15
```

Passing gates:

```text
accepted_wrong_checkpoints: 5 >= 3
accepted_wrong_success_drop_fraction: 1.0
control_accepted_wrong_rows: 0
```

## Interpretation

M1177 improves over M1169 in raw accepted row count:

```text
M1169 accepted wrong rows: 6
M1177 raw accepted wrong rows: 78
M1177 balanced accepted wrong rows: 38
```

But it does not solve the core blocker. The accepted surface is still dominated
by two physical pairs and one yaw-response target. The action-divergent export
helps find more rows on the same active set, not a new source-diverse
wrong-history boundary surface.

## Guardrail

No broad mining, actor training, PPO, promotion, private holdout, row
conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: action_divergent_bounded_relocation_reject_route_to_scarcity_audit
next: m1178-v4-public-base-action-divergent-relocation-scarcity-audit
```
