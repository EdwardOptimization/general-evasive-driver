# M806 V4 Low-Margin Boundary-Axis Expansion Design

## Purpose

M806 designs the next no-training implementation after M805 audited M804 as a
clean geometry-only diagnostic.

The question is:

```text
How should the retarget tool expand beyond obstacle-half-width so that primary
low-margin rows are source-diverse and axis-diverse enough to support the
active-steer guard corpus?
```

This milestone is design-only:

```text
no implementation
no retarget run
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Starting Evidence

M804 proved that the strict primary low-margin band is reachable:

```text
accepted_low_margin_window_rows: 252
accepted margin min: 0.000004953
accepted margin median: 0.000025013
accepted margin max: 0.000046264
```

But M804 did not pass the source-diverse guard requirement:

```text
unique_accepted_seeds: 3
required: 8

unique_accepted_source_indices: 9
required: 8

unique_accepted_fault_family_pairs: 4
required: 4

max_accepted_seed_dominance: 0.428571
required <= 0.25

max_accepted_fault_pair_dominance: 0.714286
required <= 0.40

unique_accepted_retarget_axes: 1
max_accepted_retarget_axis_dominance: 1.0
```

Axis result:

```text
obstacle_half_width accepted rows: 252
obstacle_distance accepted rows: 0
```

So the branch is not blocked by an impossible margin target. It is blocked by
retarget-axis and source concentration.

## Design Principle

M807 should reuse the M804 closed-loop replay discipline but change the search
problem:

```text
from:
  fixed half-width and fixed distance deltas around a small set of anchors

to:
  source-capped, axis-capped retarget search over multiple public axes,
  with bisection/refinement around observed collision/success transitions
```

The actor contract remains unchanged:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

M807 may retarget only public scenario geometry or simulator-side current-model
fault generation before closed-loop replay. It must not give the actor any new
input.

## Anchor Pools

M807 should consume the same M801/M804 lineage, but it must not restrict itself
to the three source seeds that produced M804 accepted rows.

Primary anchor pools:

```text
collision_edge:
  normal alpha 0.2 rows
  collision == true
  -0.001 <= margin < 0

safe_edge:
  normal alpha 0.2 rows
  success == true
  collision == false
  0 < margin <= 0.01

diagnostic_safe:
  normal alpha 0.2 rows
  success == true
  collision == false
  0.01 < margin <= 0.2
```

M807 should draw from all three pools, with caps:

```text
max rows per original seed in the accepted output: 20
max rows per original source_index in the accepted output: 12
max rows per original fault-family pair in the accepted output: 32
max rows per retarget axis in the accepted output: 48
```

These are selection caps, not replay filters. The run may replay more rows, but
accepted corpus export must be capped before declaring a pass.

## Retarget Axes

M807 should add five axis families.

### 1. Obstacle lateral offset

Shift the obstacle in body-frame lateral coordinates:

```text
body_y_delta_m:
  -0.60, -0.40, -0.25, -0.10, -0.05,
   0.05,  0.10,  0.25,  0.40,  0.60
```

This is public geometry. It tests whether different seeds and fault pairs can
enter the primary margin window by moving the obstacle sideways rather than
changing obstacle width.

Accepted rows from lateral retargeting should record:

```text
source_obstacle_body_y
target_obstacle_body_y
obstacle_y_delta_m
```

### 2. Source-step neighborhood

Replay neighboring snapshots around the source decision step:

```text
step_offset:
  -3, -2, -1, 0, +1, +2, +3
```

Implementation should collect or reconstruct exact neighboring snapshots. It
must not simply reuse the same snapshot and relabel the step. A source-step
retarget is valid only if the environment state, hidden state, and observation
come from that step.

This axis is important because M804 accepted rows were tied to a few source
indices. Neighboring snapshots may expose the same mechanism in nearby but not
identical states.

### 3. Fault activation step micro-sweep

For faults with `activation_step > 0`, collect the same seed/fault with:

```text
fault_activation_step_delta:
  -3, -2, -1, +1, +2, +3
```

Only current-model or current-model-proxy faults are allowed. The modified
fault must be applied during rollout collection before the replay snapshot is
created. It is not valid to change only metadata after a snapshot exists.

### 4. Fault severity micro-sweep

For scale-like fault parameters, create small parameter perturbations:

```text
relative capability scale delta:
  -0.08, -0.04, -0.02, +0.02, +0.04, +0.08
```

This should be interpreted according to the parameter:

```text
mu_scale, cf_scale, cr_scale, max_drive_force_scale, max_brake_force_scale,
max_steer_scale, max_steer_rate_scale:
  multiply by (1 + delta)

drive_tau_scale, steer_tau_scale:
  multiply by (1 - delta) for capability increase and (1 + abs(delta)) for
  delay increase, with the sign recorded explicitly
```

All modified values must be clamped to physically positive values and logged in
the artifact as JSON.

### 5. Bracketed distance and width bisection

M804 fixed obstacle-distance deltas produced no accepted rows, but that does
not prove distance is useless. The distance response was non-monotone on some
anchors. M807 should use bracket/refinement rather than fixed deltas:

```text
initial distance bracket:
  source x plus [-0.35, -0.25, -0.15, -0.08, -0.04, +0.04, +0.08, +0.15, +0.25, +0.35]

initial half-width bracket:
  source half-width plus [-0.010, -0.006, -0.003, +0.003, +0.006, +0.010]
```

For each anchor and axis, the implementation should:

```text
1. evaluate coarse bracket points;
2. find neighboring points whose margins cross zero or enter <=0.01;
3. bisect the active interval for up to 6 rounds;
4. stop early when 0 <= margin <= 0.00005;
5. record all evaluated points and the chosen bracket path.
```

Half-width remains a valid axis, but accepted half-width rows alone cannot pass
M807.

## Axis-Diversity Acceptance Gate

M807 should keep the M800 low-margin corpus gate and add axis-balance gates.

Primary row definition:

```text
branch == normal
alpha == 0.2
success == true
collision == false
0.0 <= min_clearance_margin <= 0.00005
metadata complete
```

Corpus pass requires:

```text
accepted rows >= 80
unique seeds >= 8
unique source_index values >= 8
unique fault-family pairs >= 4
unique retarget axes >= 3
max seed dominance <= 0.25
max source_index dominance <= 0.15
max fault-family-pair dominance <= 0.40
max retarget-axis dominance <= 0.60
normal collision rate in accepted rows == 0.0
actor checksum unchanged
residual-head checksum unchanged
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

Recommended per-axis minimum:

```text
at least 10 accepted rows from at least 3 axes
```

This prevents M807 from passing by repeating the M804 half-width result.

## Diagnostic Outputs

M807 should write:

```text
runs/m807_v4_low_margin_boundary_axis_expansion/axis_anchor_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/axis_plan_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/axis_replay_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/accepted_axis_balanced_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/rejected_axis_candidates.csv
runs/m807_v4_low_margin_boundary_axis_expansion/axis_balance_summary.csv
runs/m807_v4_low_margin_boundary_axis_expansion/source_balance_summary.csv
runs/m807_v4_low_margin_boundary_axis_expansion/bracket_trace_rows.csv
runs/m807_v4_low_margin_boundary_axis_expansion/progress.jsonl
runs/m807_v4_low_margin_boundary_axis_expansion/summary.json
docs/m807-v4-low-margin-boundary-axis-expansion-implementation.md
```

Each replay row should include:

```text
retarget_axis
retarget_axis_family
source_obstacle_body_x
source_obstacle_body_y
target_obstacle_body_x
target_obstacle_body_y
target_obstacle_half_width
obstacle_x_delta_m
obstacle_y_delta_m
half_width_delta_m
source_step
target_step
step_offset
fault_activation_step_delta
fault_severity_delta
modified_fault_params_json
bracket_round
bracket_parent_candidate_id
```

## Result Classes

M807 should classify results explicitly:

```text
v4_low_margin_boundary_axis_expansion_pass
v4_low_margin_boundary_axis_expansion_sparse
v4_low_margin_boundary_axis_expansion_source_concentrated
v4_low_margin_boundary_axis_expansion_axis_concentrated
v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic
v4_low_margin_boundary_axis_expansion_contract_violation
v4_low_margin_boundary_axis_expansion_replay_error
```

Only `v4_low_margin_boundary_axis_expansion_pass` can admit an active-steer
guard calibration design or implementation. Any diagnostic result requires an
audit first.

## Proposed M807 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_low_margin_boundary_axis_expansion \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --reference-replay-rows runs/m801_v4_low_margin_source_diverse_reference_replay/replay_rows.csv \
  --m804-replay-rows runs/m804_v4_low_margin_boundary_window_retarget/retarget_replay_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m807_v4_low_margin_boundary_axis_expansion \
  --alpha 0.2 \
  --primary-margin-threshold 0.00005 \
  --collision-margin-floor -0.001 \
  --safe-margin-ceiling 0.01 \
  --diagnostic-safe-margin-ceiling 0.2 \
  --min-rows 80 \
  --min-seeds 8 \
  --min-source-indices 8 \
  --min-fault-pairs 4 \
  --min-retarget-axes 3 \
  --max-seed-dominance 0.25 \
  --max-source-index-dominance 0.15 \
  --max-fault-pair-dominance 0.40 \
  --max-axis-dominance 0.60 \
  --device cpu
```

## Implementation Notes

M807 should extend the existing M804 module or create a sibling module:

```text
src/autodrift/v4_low_margin_boundary_axis_expansion.py
tests/test_v4_low_margin_boundary_axis_expansion.py
```

Use the M804 module for:

```text
anchor selection
closed-loop residual replay
checksum discipline
accepted-row export conventions
progress logging
```

Add focused tests for:

```text
lateral-offset plan generation
axis-balanced accepted-row selection
source caps before pass classification
bracket trace construction
fault-parameter micro-sweep clamping
```

## Stop Conditions

M807 must stop and classify instead of pushing into calibration if:

```text
accepted rows < 80
unique retarget axes < 3
max retarget-axis dominance > 0.60
max seed dominance > 0.25
max fault-pair dominance > 0.40
actor or residual checksums change
accepted rows require private holdout feedback
```

If M807 creates many rows but still only from geometry axes, it should be
classified as:

```text
v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic
```

That would trigger an audit or workflow synthesis before another retargeting
milestone.

## Forbidden Shortcuts

M807 must not:

```text
weaken the primary <=0.00005 m threshold
weaken seed/source/fault dominance thresholds
count M804 half-width rows alone as pass evidence
count collision rows as successes
post-process obstacle radius after rollout
use private holdout feedback
train the actor
train the M761 residual head
train a calibrator
run PPO
promote a checkpoint
claim true wheel-level faults from current single-track proxy data
```

## Supported Design Claim

M806 supports only this claim:

```text
The next highest-leverage step is a no-training source-diverse boundary-axis
expansion, not active-steer calibration or another half-width-only retarget.
```

It does not claim that M807 will pass or that the driver improved.

## Next Blocker

```text
m807-v4-low-margin-boundary-axis-expansion-implementation
```

M807 should implement and run the no-training axis expansion. Residual
calibration, PPO, actor mutation, residual-head mutation, and promotion remain
blocked until a source-diverse, axis-diverse primary low-margin corpus exists
and is audited.
