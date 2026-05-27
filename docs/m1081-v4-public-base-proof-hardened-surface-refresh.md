# M1081 V4 Public Base Proof Hardened Surface Refresh

## Purpose

M1081 runs the M1080 pre-registered source-diverse protected/preference surface
refresh for the M1078 proof-hardened public-gate base.

It does not train, run PPO, promote, or use private holdout.

## Matched-Current Mining

```text
candidate_pair_count: 391545
accepted_pair_count: 3129
accepted_physical_pair_count: 220
accepted_left_step_count: 26
accepted_source_obstacle_bucket_count: 19
ambiguity_surface_found: true
```

Matched-current ambiguity is not the blocker.

## Outcome Gate

```text
input_pair_count: 3129
outcome_row_count: 18774
outcome_summary_rows: 72
```

The outcome stage completed and produced enough rows for boundary relocation.

## Boundary Relocation

```text
candidate_count: 3129
row_count: 109605
accepted_wrong_history_rows: 252
accepted_wrong_history_pairs: 88
accepted_reset_rows: 9018
accepted_zero_current_rows: 1774
wrong_history_success_drop_count: 192
surface_found: true
```

The surface exists and is not sparse at the raw boundary-relocation level.

## Robustness Gates

All robustness bucket widths failed with the same top-level decision:

```text
decision: reject_duplicate_dominated_boundary_surface
passed: false
```

Primary `0.005` bucket metrics:

```text
accepted_wrong_rows: 252
accepted_wrong_physical_pairs: 9
accepted_wrong_left_steps: 6
accepted_wrong_checkpoints: 4
accepted_wrong_targets: 2
accepted_wrong_normal_margin_buckets: 7
accepted_wrong_success_drop_fraction: 0.7619047619
max_rows_per_physical_pair_fraction: 0.253968254
control_accepted_wrong_rows: 0
```

Failed gates:

```text
accepted_wrong_physical_pairs: 9 < 10
accepted_wrong_success_drop_fraction: 0.7619047619 < 1.0
max_rows_per_physical_pair_fraction: 0.253968254 > 0.25
```

Passed gates:

```text
accepted_wrong_rows >= 80
left_steps >= 5
checkpoints >= 3
targets >= 2
margin_buckets >= 2
control_accepted_wrong_rows == 0
```

## Interpretation

M1081 is a negative but useful surface-refresh result. The promoted base still
has wrong-history-sensitive boundary regions, but the accepted surface is not
robust enough for conversion:

```text
not sparse overall;
not a bucket-width artifact;
not actor-contract or training artifact;
but too few robustness-level physical pairs and too many accepted rows are not
actual success drops.
```

This means the next step should retarget sampling and boundary relocation. It
should not loosen the robustness gates or convert this surface directly.

## Decision

```text
proof_hardened_surface_refresh_duplicate_dominated_route_to_retarget_design
```

Next:

```text
m1082-v4-public-base-proof-hardened-surface-retarget-design
```
