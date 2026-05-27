# M1104 V4 Public Base Family-Intersection Target-Policy Materialization Implementation

## Purpose

M1104 implements and runs the `proof_current` target-policy materializer designed
in M1103.

This milestone reads existing M1102/M1099 artifacts only. It does not train, run
PPO, run replay, run objective optimization, mine rows, promote a checkpoint,
use private holdout, change actor inputs, or write an objective NPZ.

## Implementation

Added:

```text
src/autodrift/family_intersection_target_policy_materialization.py
tests/test_family_intersection_target_policy_materialization.py
```

The materializer:

1. reads M1102 `family_intersection_rows.csv`;
2. reads M1099 `cross_family_replay_rows.csv`;
3. joins each family row to the `proof_current` replay row;
4. uses `proof_current` replay margins, success flags, and first actions as
   objective fields;
5. preserves original source metadata and source-row metrics under source or
   diagnostic fields;
6. validates the output with `validate_boundary_row_frame`;
7. writes source and target summaries plus materialization summary JSON.

## Command

```text
PYTHONPATH=src python -m autodrift.family_intersection_target_policy_materialization \
  --family-intersection-rows-csv runs/m1102_family_aggregate_intersection_selector/family_intersection_rows.csv \
  --cross-family-replay-rows-csv runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv \
  --target-policy-label proof_current \
  --run-dir runs/m1104_target_policy_materialization
```

## Artifacts

```text
runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv
runs/m1104_target_policy_materialization/proof_current_source_summary.csv
runs/m1104_target_policy_materialization/proof_current_target_summary.csv
runs/m1104_target_policy_materialization/proof_current_materialization_summary.json
```

## Result

Materialization passes:

```text
rows: 133
expected_rows: 133
normal_success_count: 133
wrong_history_success_count: 0
success_drop_count: 133
finite_objective_rows: 133
decision: target_policy_materialization_pass
passed: true
```

Diversity gate:

```text
physical_pairs: 14
source_labels: 4
targets: 3
left_steps: 9
max_physical_pair_fraction: 0.150376
max_source_label_fraction: 0.368421
gate_pass: true
```

Source distribution:

```text
proof_current: 39 rows, 4 physical pairs, 2 targets
short61049:   27 rows, 7 physical pairs, 2 targets
short61050:   18 rows, 5 physical pairs, 3 targets
short61051:   49 rows, 11 physical pairs, 3 targets
```

Target distribution:

```text
future_braking_deceleration: 49 rows, 6 physical pairs, 4 source labels
future_lateral_accel_response: 5 rows, 1 physical pair, 2 source labels
future_yaw_response: 79 rows, 7 physical pairs, 4 source labels
```

The closest wrong-history margins remain negative:

```text
overall max wrong-history margin: -0.0000250698
overall min margin gap: 0.00151679
```

## Interpretation

The materialized `proof_current` boundary rows are now objective-ready as CSV
input for the existing boundary-outcome corpus builder. They are still not an
objective NPZ and not a trained checkpoint.

The next step should design the corpus/objective sanity run that consumes:

```text
runs/m1104_target_policy_materialization/proof_current_boundary_rows.csv
```

with the single checkpoint policy:

```text
proof_current=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

## Decision

```text
target_policy_materialization_pass_route_to_objective_corpus_design
```

Next:

```text
m1105-v4-public-base-materialized-objective-corpus-design
```

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_family_intersection_target_policy_materialization.py
```

Result:

```text
5 passed
```

Compile check:

```text
PYTHONPATH=src python -m compileall -q src tests
```

Result: passed.

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```
