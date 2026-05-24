# M518 Projection-Aware Boundary Outcome Gate

## Purpose

M518 implements and runs the projection-aware outcome gate designed in M517.
The gate replays M516 terminal-boundary projected rows while preserving the
relocated obstacle geometry, then compares projected normal, wrong-history, and
reset/zero controls.

This milestone does not train, run PPO, change actor inputs, update a
checkpoint, or promote a checkpoint.

## Command

Smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.projection_aware_boundary_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
  --pairs-csv runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv \
  --tail-offsets 0,2 \
  --max-continuation-steps 16 \
  --max-pairs-per-checkpoint-target 4 \
  --device cpu \
  --run-dir runs/m518_projection_aware_boundary_outcome_gate_smoke
```

Formal:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.projection_aware_boundary_outcome_gate \
  --checkpoint-policy m399=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --env-config-map boundary_short_reveal=configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json \
  --env-config-map boundary_warmup=configs/m502_natural_boundary_pressure_warmup_zero_relvel.json \
  --pairs-csv runs/m516_boundary_mechanism_projection_selector/targeted_pairs.csv \
  --tail-offsets 0,2,4,8 \
  --max-continuation-steps 80 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m518_projection_aware_boundary_outcome_gate
```

## Artifacts

```text
runs/m518_projection_aware_boundary_outcome_gate/summary.json
runs/m518_projection_aware_boundary_outcome_gate/projected_outcomes.csv
runs/m518_projection_aware_boundary_outcome_gate/projected_invalid_pairs.csv
runs/m518_projection_aware_boundary_outcome_gate/projected_variant_summary.csv
```

## Implementation

M518 adds:

```text
src/autodrift/projection_aware_boundary_outcome_gate.py
tests/test_projection_aware_boundary_outcome_gate.py
```

The implementation:

1. reads the M516 targeted projection rows;
2. reconstructs requested left and right outcome snapshots at
   `left_step + tail_offset` and `right_step + tail_offset`;
3. relocates the left snapshot obstacle to
   `projected_obstacle_body_x/y` and projected half-width;
4. replays `normal_projected`, `wrong_projected_once`,
   `reset_projected`, `zero_current_projected`, and
   `zero_action_history_projected`;
5. writes per-row outcomes, invalid tail-pair diagnostics, variant summaries,
   and a classification summary.

The existing tail-aligned gate was intentionally not reused because it would
reconstruct original obstacle geometry and invalidate the M516 projection proof
surface.

## Result

Summary:

```text
classification:                                  invalid_projection_replay
input_pair_count:                                239
valid_tail_pair_count:                           638
invalid_tail_pair_count:                         318
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
invalid rows total: 318

by tail_offset:
  8: 239
  4: 48
  2: 31

missing_left_tail:
  true: 318

missing_right_tail:
  false: 318

by config:
  boundary_short_reveal: 213
  boundary_warmup:       105

by target:
  future_braking_deceleration:    159
  future_lateral_accel_response:   80
  future_yaw_response:             79
```

`tail_offset=8` is invalid for every one of the `239` input rows. The failure is
not that projected replay cannot run; it is that the pre-registered offset set
included a late offset that near-terminal left snapshots cannot satisfy.

## Interpretation

M518 is a negative gate result, but the failure is an offset/replay validity
failure, not a controller failure:

```text
projection-aware implementation:        works
relocated obstacle geometry preserved:  yes
actor contract changed:                 no
training or promotion performed:        no
wrong-history outcome proof:            not established
gate classification:                    invalid_projection_replay
```

The single wrong-history proof candidate is source-narrow and has zero event
rows, so it should not be treated as positive mechanism proof. Controls show a
small number of margin-only rows, also with zero event rows.

Because invalid rows exceed the input pair count, M518 cannot decide whether
the M516 mechanism surface is fast-corrected or genuinely no-effect under valid
projection-aware replay. The next step should fix the offset validity issue and
rerun the same gate logic without changing actor inputs or promoting a
checkpoint.

## Decision

```text
reject_invalid_projection_replay
```

Failure classification:

```text
scenario_sampling_failure
```

Next blocker:

```text
m519-valid-offset-projection-outcome-redesign
```
