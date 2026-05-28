# M1290 Paper-Route Source-History Directional Conflict Audit

## Summary

M1290 implements and runs a no-training audit of the M1288 before/after
source-history objective rows.

Decision:

```text
source_history_directional_conflict_magnitude_compression_route_to_directional_repair_design
```

Result class:

```text
source_history_directional_conflict_magnitude_compression
```

M1290 confirms that M1288 reduced exact loss by shrinking residual magnitudes,
but did not solve row-wise correct-history versus wrong-history directionality.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_source_history_directional_conflict_audit.py
```

Result:

```text
2 passed in 0.96s
```

Audit:

```bash
PYTHONPATH=src python -m autodrift.source_history_directional_conflict_audit \
  --before-rows runs/m1288_source_history_objective_only_update/source_history_objective_rows_before.csv \
  --after-rows runs/m1288_source_history_objective_only_update/source_history_objective_rows_after.csv \
  --run-dir runs/m1290_source_history_directional_conflict_audit
```

## Implementation

Added:

```text
src/autodrift/source_history_directional_conflict_audit.py
tests/test_source_history_directional_conflict_audit.py
```

The tool joins M1288 before/after rows by:

```text
history_intervention_id
intervention_id
pair_id
```

Then it writes:

```text
runs/m1290_source_history_directional_conflict_audit/summary.json
runs/m1290_source_history_directional_conflict_audit/directional_conflict_rows.csv
```

## Sign Quadrants

Before M1288:

```text
correct_positive_wrong_positive: 0
correct_positive_wrong_negative: 76
correct_negative_wrong_positive: 76
correct_negative_wrong_negative: 0
```

After M1288:

```text
correct_positive_wrong_positive: 0
correct_positive_wrong_negative: 76
correct_negative_wrong_positive: 76
correct_negative_wrong_negative: 0
```

Directional gate:

```text
before_both_directional_fraction: 0.0
after_both_directional_fraction: 0.0
after_mutually_exclusive_count: 152
after_mutually_exclusive_fraction: 1.0
after_both_positive_count: 0
quadrant_changed_count: 6
```

Interpretation:

```text
Every row remains mutually exclusive after M1288: one of correct-history or
wrong-history preference has the right sign, but never both.
```

## Loss And Margin Movement

Loss:

```text
loss_improved_count: 152
loss_improved_fraction: 1.0
combined_loss_delta_mean: -11.4311475093
combined_loss_delta_p50: -13.2336899258
combined_loss_delta_min: -14.0310711383
combined_loss_delta_max: -0.5453297538
```

Margin magnitude:

```text
min_abs_preference_margin_delta_mean: -11.5622198707
min_abs_preference_margin_delta_p50: -13.4330395460
min_abs_margin_decreased_count: 152
min_abs_margin_decreased_fraction: 1.0
```

Interpretation:

```text
The update improves loss for every row, but it decreases the smaller absolute
preference margin for every row. That is magnitude compression, not row-wise
directional repair.
```

## Pair Structure

The audit finds:

```text
pair_probe_group_count: 76
pair_probe_group_size_min: 2
pair_probe_group_size_max: 2
```

This matches the expected paired source-history structure. The next repair
design should treat these two-row pair/probe groups as first-class units rather
than independently minimizing scalar loss on individual rows.

## Decision

Do not continue with blind actor-head updates:

```text
M1288 already shows scalar exact loss can improve while preserving the
mutually-exclusive sign pattern.
```

Do not start PPO:

```text
The source-history policy-side directional relation is still not positive.
```

Next:

```text
m1291-paper-route-source-history-directional-repair-design
```

M1291 should design a no-PPO row-wise directional repair path. It should decide
whether the next implementation is:

```text
a crossing-aware actor_mean continuation probe;
a pair-group directional objective;
a trainable-scope escalation beyond actor_mean;
or a source-history corpus relabel/refresh audit.
```

## Claim Discipline

M1290 supports:

```text
The M1288 exact-loss improvement is a magnitude-compression update, not a
row-wise directional source-history repair.
```

M1290 does not support:

```text
promotion;
PPO readiness;
closed-loop driver improvement;
paper-level evidence;
level3 anticipatory self-identification.
```

PPO and promotion remain blocked.
