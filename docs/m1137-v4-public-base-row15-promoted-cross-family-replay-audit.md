# M1137 V4 Public Base Row15 Promoted Cross-Family Replay Audit

## Purpose

M1137 audits the M1136 cross-family replay report before any objective
conversion or training.

This milestone is audit-only. It does not run replay, optimize an objective,
train actor weights, run PPO, promote, use private holdout, or change actor
inputs.

## Source Gate Recap

M1136 source-policy source-row replay passed:

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

Therefore the M1134 aggregate export is valid as a source-policy proof surface.

## Cross-Family Failure Scope

M1136 cross-family artifacts:

```text
cross_family_replay_rows: 860
cross_family_summary_rows: 65
duplicate_geometry_summary_rows: 460
failed_duplicate_geometry_groups: 34
```

Failures are not metadata loss; they are mostly non-source policies making some
wrong-history branches safe. This blocks direct mixed-family objective
optimization.

## All-Policy Intersection Audit

Reading only the existing `cross_family_replay_rows.csv`, the all-policy
intersection is still broad:

```text
family_rows: 172
all_policy_pass_rows: 148
physical_pairs: 13
left_steps: 6
targets: 2
max_pair_count: 20
max_pair_fraction: 0.135135
```

Source-label distribution among all-policy-pass rows:

```text
short61051: 42
short61049: 41
short61050: 32
row15_current: 28
previous_m1078_base: 5
```

Target distribution:

```text
future_braking_deceleration: 78
future_yaw_response: 70
```

The intersection loses lateral-accel rows but remains strong enough for a
family-intersection selector route:

```text
rows >= 100
physical_pairs >= 12
left_steps >= 6
targets >= 2
max_pair_fraction <= 0.25
```

## Route Decision

The audit rejects direct mixed-family objective optimization because cross-family
failures exist. It also does not need to fall back to source-specific objective
corpora or target-base materialization yet, because the all-policy intersection
is sufficiently broad.

Recommended next route:

```text
family-intersection replay-calibrated rows
```

M1138 should design a deterministic selector using existing
`family_aggregate_intersection_selector` semantics. It should keep only rows
that pass normal-history success and wrong-history failure under all five family
policies, preserve source metadata, and require at least:

```text
rows >= 100
physical_pairs >= 12
left_steps >= 6
source labels >= 4
targets >= 2
max rows per physical pair fraction <= 0.25
```

## Decision

```text
row15_promoted_cross_family_audit_route_to_intersection_selector_design
```

Next:

```text
m1138-v4-public-base-row15-promoted-intersection-selector-design
```
