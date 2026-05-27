# M1102 V4 Public Base Family-Aggregate Intersection Selector Implementation

## Purpose

M1102 implements and runs the deterministic family-intersection selector designed
in M1101.

This milestone reads existing M1097/M1099 artifacts only. It does not train, run
PPO, run replay, run objective optimization, mine rows, promote a checkpoint,
use private holdout, or change actor inputs.

## Implementation

Added:

```text
src/autodrift/family_aggregate_intersection_selector.py
tests/test_family_aggregate_intersection_selector.py
```

The selector:

1. reads M1097 `family_aggregate_boundary_rows.csv`;
2. reads M1099 `cross_family_replay_rows.csv`;
3. groups replay results by `family_row_id`;
4. keeps a family row only if every expected policy preserves
   normal-history success and wrong-history failure;
5. writes kept rows, dropped rows, a policy pass matrix, source/target summaries,
   and summary JSON;
6. fails closed if diversity thresholds are not met.

## Command

```text
PYTHONPATH=src python -m autodrift.family_aggregate_intersection_selector \
  --family-rows-csv runs/m1097_family_aggregate_boundary_conversion/family_aggregate_boundary_rows.csv \
  --cross-family-replay-rows-csv runs/m1099_family_aggregate_replay_sanity/cross_family_replay_rows.csv \
  --run-dir runs/m1102_family_aggregate_intersection_selector \
  --expected-policy proof_current \
  --expected-policy short61049 \
  --expected-policy short61050 \
  --expected-policy short61051
```

## Artifacts

```text
runs/m1102_family_aggregate_intersection_selector/family_intersection_rows.csv
runs/m1102_family_aggregate_intersection_selector/dropped_cross_family_rows.csv
runs/m1102_family_aggregate_intersection_selector/policy_pass_matrix.csv
runs/m1102_family_aggregate_intersection_selector/source_summary.csv
runs/m1102_family_aggregate_intersection_selector/target_summary.csv
runs/m1102_family_aggregate_intersection_selector/summary.json
```

## Result

Selector output:

```text
family_rows: 146
replay_rows: 584
kept_rows: 133
dropped_rows: 13
decision: family_aggregate_intersection_selector_pass
passed: true
```

Diversity gate:

```text
rows: 133
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

The `13` dropped rows match the M1100 cross-family failure set.

## Interpretation

The selector succeeds: a replay-calibrated all-policy intersection exists and
preserves enough diversity for the next conversion step.

However, do not feed `family_intersection_rows.csv` directly into the existing
boundary-outcome objective. The selected rows still carry their original source
checkpoint labels and source-row metrics. The existing objective path builds
exactly one checkpoint corpus per run to avoid hidden-state-space mixing.

The next step should design target-policy materialization:

```text
family_intersection_rows
  + M1099 replay rows for one target policy
  -> objective-ready rows with checkpoint_label = target policy
```

This keeps the selector's cross-family proof filter while using one target
policy's replay-calibrated margins and hidden states for objective construction.

## Decision

```text
family_aggregate_intersection_selector_pass_route_to_target_policy_materialization_design
```

Next:

```text
m1103-v4-public-base-family-intersection-target-policy-materialization-design
```

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_family_aggregate_intersection_selector.py
```

Result:

```text
6 passed
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
