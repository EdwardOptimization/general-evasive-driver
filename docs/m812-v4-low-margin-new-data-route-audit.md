# M812 V4 Low-Margin New Data Route Audit

## Purpose

M812 audits M811 before any further data generation, residual calibration, PPO,
or promotion.

The audit question is:

```text
Is M811's zero-primary result a fixed-grid boundary-resolution miss, a route
failure, or an instrumentation artifact?
```

M812 is audit-only:

```text
no training
no residual calibration
no PPO
no checkpoint promotion
no threshold weakening
```

## M811 Result Recap

M811 produced:

```text
source_groups: 96
source_snapshots: 192
boundary_search_replay_rows: 2688
replay_errors: 0
warmup_artifact_rows: 0
accepted_primary_raw_rows: 0
accepted_primary_rows: 0
result_class: v4_low_margin_new_data_route_sparse
```

Contract invariants passed:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

This rules out the main instrumentation failures:

- the sparse result is not caused by replay errors;
- the sparse result is not caused by warm-up probe artifacts;
- the sparse result is not caused by actor or residual-head mutation;
- the sparse result is not a promotion or PPO result.

## Margin Distribution

M811 replay margin bands:

```text
collision_negative: 542
primary_0_to_5e-5: 0
near_5e-5_to_1e-3: 0
near_1e-3_to_1e-2: 6
wide_1e-2_to_5e-2: 26
wide_over_5e-2: 2114
nonfinite: 0
```

The closest row to the primary target was still collision-side:

```text
margin: -0.0007608713848834547
distance_to_target: 0.0007858713848834547
seed: 78059
source_group_id: 83
source_index: 167
warmup_mode: natural_policy
fault_family_pair: drive_authority_drop->nominal
boundary_axis: obstacle_lateral_offset
plan_reason: source_group_lateral_offset
```

The smallest safe margin found was:

```text
min_positive_margin: 0.0029221692398473387
```

That is far outside the strict primary window:

```text
primary window: 0.0 <= margin <= 0.00005
```

## Boundary Brackets

M811 did not simply fail to find collision/safe boundary structure.

Existing replay rows contain collision/safe brackets:

```text
snapshot_axis_brackets: 48
bracket_axes:
  obstacle_lateral_offset: 40
  obstacle_timing: 8
snapshot_brackets_any_axis: 40
```

But the brackets are too coarse:

```text
minimum snapshot-axis bracket gap: 0.015385162709582234
median snapshot-axis bracket gap: 0.09097610223582464
```

Closest bracket:

```text
axis: obstacle_timing
negative_margin: -0.008752357238026143
positive_margin: 0.006632805471556091
gap: 0.015385162709582234
source_group_id: 65
snapshot_uid: 65:131:24
```

Closest obstacle-lateral bracket:

```text
axis: obstacle_lateral_offset
negative_margin: -0.0007608713848834547
positive_margin: 0.021337002096252444
gap: 0.0220978734811359
source_group_id: 83
snapshot_uid: 83:167:24
```

This supports a specific diagnosis:

```text
M811 created usable collision/safe edges, but fixed candidate deltas jumped
over the narrow low-margin band.
```

## Failure Classification

Primary classification:

```text
scenario_sampling_failure
```

More precise subtype:

```text
fixed_grid_boundary_resolution_miss
```

Secondary risks:

```text
metric_artifact
objective_overfit
```

Those secondary risks would apply if the project tried to train from M811 or
M804/M807 geometry-only rows despite the sparse/source-diversity blocker.

## Supported Claims

M812 supports:

- M811's implementation is runnable and preserves the no-training contract;
- active warm-up and joint fault/obstacle timing can generate diverse replay coverage;
- M811 contains real collision/safe boundary brackets;
- the immediate blocker is boundary resolution, not replay corruption or checksum mutation.

## Falsified Claims

M812 falsifies:

- the current fixed-grid M811 candidate set is enough to populate the strict primary window;
- another calibration step is justified before source-diverse primary rows exist;
- sparse zero-primary output can be treated as a pass;
- threshold relaxation is necessary before trying adaptive bracketing.

## Decision

Decision:

```text
admit_adaptive_boundary_bracketing_design
```

M812 does not admit:

```text
residual calibration
PPO
checkpoint promotion
primary threshold relaxation
geometry-only pass claims
true wheel-level fault claims
```

Next blocker:

```text
m813-v4-adaptive-boundary-bracketing-design
```

M813 should design adaptive closed-loop bracketing over M811 collision/safe
edges. It should preserve:

- alpha `0.2`;
- the primary `0.00005` margin threshold;
- source/fault/warm-up/axis diversity gates;
- actor and residual-head checksum invariants;
- current-model proxy-fault claim limits.

The design should avoid another wide fixed-grid route. The useful unit is a
snapshot-axis bracket with one collision-side and one safe-side candidate, then
a deterministic bracket refinement procedure that resolves the primary window
without using primary-window success to justify training or promotion.
