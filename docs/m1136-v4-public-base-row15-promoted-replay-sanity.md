# M1136 V4 Public Base Row15 Promoted Replay Sanity

## Purpose

M1136 runs the M1135 pre-registered source-aware replay sanity command for the
M1134 family aggregate rows.

This milestone runs replay only. It does not optimize an objective, train actor
weights, run PPO, promote, use private holdout, or change actor inputs.

## Command Result

Artifact:

```text
runs/m1136_row15_promoted_family_aggregate_replay_sanity/summary.json
```

Top-level result:

```text
decision: family_aggregate_replay_sanity_source_gate_pass
passed: true
family_rows: 172
replay_rows: 860
source_policy_replay_rows: 172
cross_family_summary_rows: 65
duplicate_geometry_summary_rows: 460
failed_duplicate_geometry_groups: 34
training_started: false
ppo_used: false
objective_optimization_started: false
promoted: false
private_holdout_used: false
actor_inputs_changed: false
```

## Source-Policy Gate

Each source policy reproduces its own source rows:

```text
previous_m1078_base:  7/7 normal success, 0 wrong-history success, 7/7 success drops
row15_current:       28/28 normal success, 0 wrong-history success, 28/28 success drops
short61049:          51/51 normal success, 0 wrong-history success, 51/51 success drops
short61050:          37/37 normal success, 0 wrong-history success, 37/37 success drops
short61051:          49/49 normal success, 0 wrong-history success, 49/49 success drops
```

Aggregate source gate:

```text
source_row_count: 172
normal_success_count: 172
wrong_history_success_count: 0
success_drop_count: 172
physical_pairs: 15
checkpoints: 5
targets: 3
gate_pass: true
```

This verifies that the M1134 export preserves the intended source-policy
normal-history success and wrong-history failure relation.

## Cross-Family Report

Cross-family replay is a report, not a pass/fail gate for this milestone.
It shows that the aggregate rows should not be used directly as a mixed-family
objective:

```text
cross_family_replay_rows: 860
cross_family_summary_rows: 65
failed_duplicate_geometry_groups: 34
```

Several failures are wrong-history branches becoming safe under non-source
policies. Examples include:

```text
previous_m1078_base on short61049 braking rows:
  wrong_history_success_rate: 0.115385
  failed rows: 146,156,157

row15_current on short61049 braking rows:
  wrong_history_success_rate: 0.192308
  failed rows: 116,117,146,156,157

row15_current on short61050 lateral rows:
  wrong_history_success_rate: 1.0
  failed row: 170
```

The source-policy gate passes, but cross-family compatibility is not automatic.

## Interpretation

M1136 validates the M1134 aggregate export as a source-policy proof surface.
It does not validate direct mixed-family objective optimization.

The next step should audit the cross-family report and choose one of:

```text
family-intersection replay-calibrated rows
source-specific objective corpora
target-base rebuilt hidden-state rows
```

## Decision

```text
row15_promoted_replay_sanity_source_gate_pass_route_to_cross_family_audit
```

Next:

```text
m1137-v4-public-base-row15-promoted-cross-family-replay-audit
```
