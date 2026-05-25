# M861 V4 Closer Obstacle Source Generation Audit

## Purpose

M861 audits the M860 no-training closer obstacle/source generation result before
any pair-delta replay, objective training, PPO, or broader source generation.

The audit question is:

```text
Did M860 create enough new low-margin boundary coverage for pair-delta mining,
or should the branch refine generated brackets first?
```

M861 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
no pair-delta sequence replay
```

## Artifact Completeness

M860 produced the required artifacts:

```text
runs/m860_v4_closer_obstacle_source_generation/summary.json
runs/m860_v4_closer_obstacle_source_generation/generation_plan_rows.csv
runs/m860_v4_closer_obstacle_source_generation/generated_replay_rows.csv
runs/m860_v4_closer_obstacle_source_generation/accepted_generated_boundary_rows.csv
runs/m860_v4_closer_obstacle_source_generation/all_accepted_generated_rows.csv
runs/m860_v4_closer_obstacle_source_generation/pairability_projection_rows.csv
runs/m860_v4_closer_obstacle_source_generation/source_generation_summary.csv
runs/m860_v4_closer_obstacle_source_generation/gate_summary.csv
runs/m860_v4_closer_obstacle_source_generation/rejected_rows.csv
```

Frozen-parameter checks passed:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
pair_delta_sequence_replay_used: false
promoted: false
```

## Main Result

M860 generated broad candidate coverage:

```text
generation_plan_rows: 660
primary_source_groups_planned: 44
primary_seed_count_planned: 8
primary_fault_family_count_planned: 9
snapshot_rejection_rows: 0
```

But accepted boundary coverage stayed below sparse gate:

```text
accepted_generated_boundary_rows: 17 < 32
accepted_boundary_new_to_m844_rows: 17 < 24
unique_source_group_count: 17
unique_seed_count: 4 < 5
unique_fault_family_count: 8
unique_boundary_axis_count: 2
pairability_projection_rows: 38 < 40
```

Result class:

```text
v4_closer_obstacle_source_generation_source_limited
```

## Route-Specific Evidence

Accepted rows came only from all-safe closer-obstacle generation:

```text
all_safe_closer_obstacle: 570 replay rows, 17 accepted
all_collision_safer_side: 90 replay rows, 0 accepted
```

By axis:

```text
obstacle_lateral_offset: 220 replay rows, 14 accepted
obstacle_timing: 220 replay rows, 3 accepted
obstacle_half_width: 220 replay rows, 0 accepted
```

All-collision safer-side rows remained collision/negative:

```text
all_collision_safer_side:
  negative rows: 90
  boundary rows: 0
  wide rows: 0
  max margin: -0.001050
```

This means the all-collision family is close to the boundary, but the first
coarse safer-side grid did not cross into positive margin.

All-safe closer-obstacle rows were mixed:

```text
all_safe_closer_obstacle:
  negative rows: 68
  boundary rows: 17
  wide rows: 485
```

This is not merely an all-wide failure. The generated grid crossed the boundary
for some source/axis families but often jumped over the accepted window.

## Generated Bracket Audit

Grouping M860 generated replay rows by:

```text
source_group_id
step
boundary_axis
generation_family
```

gives:

```text
groups with accepted boundary row: 17
groups with wide/negative bracket but no accepted row: 13
groups all wide: 84
groups all negative: 18
```

Representative bracket examples:

```text
source_group=62 axis=obstacle_lateral_offset:
  -1.393 -> margin 0.2091
  -1.243 -> margin 0.0596
  -1.043 -> margin -0.0466

source_group=14 axis=obstacle_lateral_offset:
  -1.306 -> margin 0.2911
  -1.156 -> margin 0.1436
  -0.956 -> margin -0.0018

source_group=57 axis=obstacle_lateral_offset:
  -1.645 -> margin 0.3263
  -1.495 -> margin 0.1776
  -1.295 -> margin -0.0072
```

The important implication is:

```text
M860 did not only fail from missing source diversity.
It also exposed generated wide/negative brackets that are refinement-ready.
```

If those 13 no-boundary brackets can be refined into accepted rows, M860-family
coverage may approach or exceed the sparse gates without changing actor inputs
or running pair-delta replay.

## Interpretation

Supported claims:

```text
M860 generation-plan coverage is broad.
M860 preserves the P0 actor and M761 residual-head contracts.
All-safe closer-obstacle generation opens real new boundary-new-to-M844 rows.
The generated replay surface contains bracketable source/axis families.
```

Unsupported claims:

```text
M860 is objective-ready.
M860 is pair-delta outcome evidence.
M860 admits PPO.
M860 proves learned self-ID.
M860 justifies checkpoint promotion.
```

Failure taxonomy:

```text
scenario_sampling_failure:
  accepted rows and seed coverage are below sparse gate

metric_artifact risk:
  pairability rows are only projections and cannot be counted as sequence
  outcome evidence

contract_violation:
  not observed
```

## Decision

M861 should not route directly to pair-delta mining. The better next step is:

```text
M862 generated-boundary refinement design
```

The refinement route should:

```text
1. use M860 generated replay rows as bracket evidence;
2. select same-source same-axis wide/negative generated endpoint pairs;
3. replay no-training bisection/refinement between endpoint parameters;
4. accept only primary boundary-new-to-M844 successful non-collision rows with
   0 <= min_clearance_margin <= 0.05;
5. keep pair-delta sequence replay, objective training, PPO, and promotion
   blocked until after audit.
```

This is more targeted than broader scenario generation because M860 already
found bracketable generated rows. It is also safer than pair-delta replay
because sparse generated-boundary coverage has not passed.

Decision:

```text
admit_generated_boundary_refinement_design
```

Next:

```text
m862-v4-generated-boundary-refinement-design
```
