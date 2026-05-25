# M868 V4 Generated Boundary Pair-Delta Refresh Audit

## Purpose

M868 audits M867 before any objective conversion, PPO, checkpoint promotion, or
additional replay implementation.

The audit question is:

```text
Does M867's real but source-limited pair-delta outcome evidence admit objective
design, or should the branch first expand accepted pair-delta coverage?
```

M868 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Artifact Completeness

M867 produced the required artifacts:

```text
runs/m867_v4_generated_boundary_pair_delta_refresh/summary.json
runs/m867_v4_generated_boundary_pair_delta_refresh/pair_candidate_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/accepted_pair_delta_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/balanced_pair_delta_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/component_control_rows.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/diversity_summary.json
runs/m867_v4_generated_boundary_pair_delta_refresh/gate_summary.csv
runs/m867_v4_generated_boundary_pair_delta_refresh/rejected_rows.csv
```

Frozen-parameter checks passed:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

## Candidate Gate Result

M867 candidate selection is clean and diverse:

```text
pair_candidate_rows: 1332 >= 120
selected_replay_pairs: 118 >= 80
selected_unique_left_source_group_count: 27 >= 16
selected_unique_left_seed_count: 5 >= 5
selected_unique_left_fault_family_count: 9 >= 8
```

This means the source limitation is not caused by failing to select diverse
replay pairs. It appears after closed-loop pair-delta outcome replay.

## Pair-Delta Outcome Result

M867 is not all-weak:

```text
pair_delta_sequence_rows: 1416
accepted_pair_delta_rows: 234
accepted_pair_delta_degradation_rows: 156
accepted_pair_delta_improvement_rows: 78
pair_delta_success_flip_rows: 97
pair_delta_collision_flip_rows: 97
max_abs_margin_delta: 0.04554687977030536
```

This is actual sequence outcome evidence, not just pairability projection.

## Source Limitation

Accepted rows are concentrated by left seed:

```text
accepted_pair_delta_rows:
  78058: 192
  78050: 42

balanced_pair_delta_rows:
  78058: 16
  78050: 16
```

The selected replay set covered all five M864 seeds:

```text
selected replay left seeds:
  78058: 37
  78055: 29
  78050: 21
  78048: 17
  78057: 14
```

But the non-accepted seeds had weak pair-delta outcome response:

```text
left_seed 78048:
  max_abs_margin_delta: 0.002866466559805936
  success_flip_rows: 0
  collision_flip_rows: 0

left_seed 78055:
  max_abs_margin_delta: 0.0015455967148021443
  success_flip_rows: 0
  collision_flip_rows: 0

left_seed 78057:
  max_abs_margin_delta: 0.0011730096064392903
  success_flip_rows: 0
  collision_flip_rows: 0
```

So the current blocker is not pair construction. It is accepted outcome
sensitivity concentration.

## Balanced Corpus Gate

The balanced corpus has enough rows but not enough seed/direction balance:

```text
balanced_pair_delta_rows: 32
balanced_unique_left_source_group_count: 5
balanced_unique_left_seed_count: 2
balanced_unique_left_fault_family_count: 5
balanced_unique_fault_family_pair_count: 11
balanced_unique_hold_steps_count: 2
balanced_unique_direction_count: 2
balanced_max_left_source_group_dominance: 0.25
balanced_max_left_seed_dominance: 0.5
balanced_max_direction_dominance: 0.75
balanced_max_axis_pair_dominance: 0.96875
```

This fails the intended sparse admissibility because:

```text
unique_left_seed_count: 2 < 3
direction dominance: 0.75 > 0.60
axis-pair dominance is very high: 0.96875
```

## Component Controls

Component controls were produced only after accepted pair-delta rows existed:

```text
component_control_rows: 396
```

They are useful diagnostics but not primary pair-delta evidence:

```text
component directions are steer/throttle/brake axis probes;
they cannot satisfy primary M867 or M868 gates;
they cannot justify objective training or promotion.
```

## Interpretation

Supported claims:

```text
M867 successfully converted M864 pairability projection into real pair-delta
sequence outcome evidence.
The replay implementation is clean: no actor or residual-head mutation.
The selected replay set is diverse enough; candidate selection is not the
active blocker.
There is strong pair-delta sensitivity on a subset of M864 generated-boundary
rows.
```

Unsupported claims:

```text
M867 is objective-ready.
M867 is a source-diverse pair-delta corpus.
M867 proves learned self-identification.
M867 admits PPO or checkpoint promotion.
Component controls can replace pair-delta evidence.
```

Failure taxonomy:

```text
scenario_sampling_failure:
  accepted pair-delta rows are concentrated in left seeds 78058 and 78050.

metric_artifact:
  pairability projection was correctly separated from outcome replay, but
  component controls must remain diagnostic-only.

contract_violation:
  not observed.
```

## Decision

M868 rejects immediate objective conversion and routes to targeted accepted
pair-delta coverage expansion.

Decision:

```text
route_to_generated_boundary_pair_delta_coverage_expansion_design
```

Next:

```text
m869-v4-generated-boundary-pair-delta-coverage-expansion-design
```

The next design should target the actual blocker:

```text
1. expand accepted pair-delta coverage for left seeds 78048, 78055, and 78057;
2. reduce direction dominance, especially pair_delta_negative dominance;
3. reduce obstacle_lateral_offset axis-pair dominance;
4. keep pairability projection separate from outcome replay;
5. keep objective training, PPO, and promotion blocked until a more balanced
   accepted pair-delta corpus exists.
```
