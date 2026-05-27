# M1082 V4 Public Base Proof Hardened Surface Retarget Design

## Purpose

M1082 designs a retargeted current-base surface refresh after M1081 found a
real but non-robust wrong-history boundary surface.

This milestone does not mine rows, train, run PPO, promote, or use private
holdout.

## M1081 Failure

M1081 was not sparse:

```text
matched_current_accepted_pairs: 3129
matched_current_physical_pairs: 220
boundary_accepted_wrong_history_rows: 252
boundary_wrong_history_success_drop_count: 192
```

But the primary `0.005` robustness gate failed:

```text
accepted_wrong_physical_pairs: 9 < 10
accepted_wrong_success_drop_fraction: 0.7619047619 < 1.0
max_rows_per_physical_pair_fraction: 0.253968254 > 0.25
```

So the failure is source-diversity / success-drop quality, not lack of any
wrong-history signal.

## Retarget Principles

Do not weaken robustness thresholds. M1083 should keep:

```text
accepted_wrong_history_rows >= 80
physical_pairs >= 10
left_steps >= 5
checkpoints >= 3
targets >= 2
margin_buckets >= 2 at width 0.005
success_drop_fraction == 1.0
max_rows_per_pair_fraction <= 0.25
control_accepted_rows == 0
```

Instead, change the sampling and relocation pressure:

```text
increase probe-source coverage;
reduce per-source bucket dominance;
move relocation closer to terminal success-drop boundaries;
cap normal margin to near-boundary rows;
use obstacle body offsets to produce more distinct physical-pair successes.
```

## M1083 Changes

### Matched-Current Retarget

Use eight probe seeds and more episodes, but stricter per-source bucket caps:

```text
probe_seeds: 108200-108207
episodes: 60
max_samples: 2200
nearest_k: 16
max_pairs_per_target: 500
max_pairs_per_left_step: 12
max_pairs_per_source_obstacle_bucket: 25
min_accepted_pairs: 160
```

### Boundary Retarget

Tighten accepted rows toward actual success drops:

```text
target_normal_margins:
  0.0005,0.001,0.0025,0.005,0.01,0.02,0.04

min_base_margin_gap: 0.005
min_margin_gap: 0.04
max_normal_margin: 0.04

body_longitudinal_offsets:
  -2.0,-1.0,0.0,1.0,2.0

body_lateral_offsets:
  -0.4,0.0,0.4
```

The offsets are intended to turn more M1081-like near misses into distinct
physical-pair success drops, not to lower the acceptance bar.

## Result Classes

```text
proof_hardened_surface_retarget_pass
proof_hardened_surface_retarget_sparse
proof_hardened_surface_retarget_duplicate_dominated
proof_hardened_surface_retarget_success_drop_insufficient
proof_hardened_surface_retarget_tooling_needed
proof_hardened_surface_retarget_training_or_contract_artifact
```

If M1083 again has many raw accepted rows but success-drop fraction is below
`1.0`, route to tooling for success-drop-filtered boundary export rather than
weakening the robustness gate.

## Decision

```text
proof_hardened_surface_retarget_design_admit_m1083_refresh
```

Next:

```text
m1083-v4-public-base-proof-hardened-surface-retarget-refresh
```
