# M520 Valid-Offset Projection Outcome Gate

## Purpose

M520 reruns the projection-aware boundary outcome gate from M518 with the
valid-offset redesign from M519. It removes the globally invalid `tail_offset=8`
while preserving the same relocated-obstacle replay semantics.

This milestone does not train, run PPO, change actor inputs, update a
checkpoint, or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.projection_aware_boundary_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
  --pairs-csv runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv \
  --tail-offsets 0,2,4 \
  --max-continuation-steps 80 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m520_valid_offset_projection_outcome_gate
```

## Artifacts

```text
runs/m520_valid_offset_projection_outcome_gate/summary.json
runs/m520_valid_offset_projection_outcome_gate/projected_outcomes.csv
runs/m520_valid_offset_projection_outcome_gate/projected_invalid_pairs.csv
runs/m520_valid_offset_projection_outcome_gate/projected_variant_summary.csv
```

## Result

Summary:

```text
classification:                                  margin_only_projected_history_signal
input_pair_count:                                239
valid_tail_pair_count:                           638
invalid_tail_pair_count:                          79
outcome_row_count:                              3190
projected_variant_summary_rows:                  45
relocated_obstacle_geometry_used:              true

wrong_projected_once_total_proof_candidate_count: 1
wrong_projected_once_total_event_rows:            0
wrong_projected_once_probe_seed_count:            1
wrong_projected_once_target_count:                1
wrong_projected_once_config_count:                1
wrong_projected_once_obstacle_bucket_count:       1
wrong_projected_once_projection_bucket_count:     1
wrong_projected_once_single_seed_share:         1.0
wrong_projected_once_single_target_share:       1.0
wrong_projected_once_single_obstacle_bucket_share: 1.0
wrong_projected_once_single_projection_bucket_share: 1.0

control_total_proof_candidate_count:             10
control_total_event_rows:                         0
control_by_variant:
  reset_projected:                                8
  zero_current_projected:                         1
  zero_action_history_projected:                  1

actor_contract_changed:                       false
training_or_promotion_performed:              false
```

Invalid replay audit:

```text
invalid rows total: 79

by tail_offset:
  4: 48
  2: 31

missing_left_tail:
  true: 79

missing_right_tail:
  false: 79

by target:
  future_braking_deceleration: 79
```

Removing `tail_offset=8` resolves the M518 gate-level invalidity. The remaining
invalid rows are bounded and no longer dominate the classification.

Wrong-history variant summary:

```text
future_braking_deceleration:
  offset 0: first_action_mean 0.126979, trajectory_mean 0.107281,
            proof rows 0, events 0
  offset 2: first_action_mean 0.126032, trajectory_mean 0.109309,
            proof rows 0, events 0
  offset 4: first_action_mean 0.121128, trajectory_mean 0.106378,
            proof rows 0, events 0

future_lateral_accel_response:
  offsets 0/2/4: proof rows 0, events 0

future_yaw_response:
  offset 2: proof rows 1, events 0, max margin gap 0.167817
  offsets 0/4: proof rows 0, events 0
```

## Interpretation

M520 confirms that M518's formal failure was caused by the invalid late offset,
not by projection-aware replay itself. With valid offsets, the gate produces an
interpretable classification:

```text
margin_only_projected_history_signal
```

That is still not positive wrong-history outcome proof. The only wrong-history
proof candidate is a single source-narrow margin row with zero event rows. The
more useful signal is behavioral: wrong-history can move first actions and
short action trajectories, especially on the braking target, but the closed-loop
outcome quickly corrects before producing source-diverse success/collision or
completion events.

This supports the M517/M519 caution: do not keep forcing more artificial
one-shot wrong-history outcome rows. The next question should become whether
the online GRU recurrent belief policy adds measurable value over weaker
history baselines.

## Decision

```text
margin_only_projected_history_signal_admit_m521_history_value_ablation_design
```

Failure classification:

```text
none
```

Next blocker:

```text
m521-history-value-ablation-design
```
