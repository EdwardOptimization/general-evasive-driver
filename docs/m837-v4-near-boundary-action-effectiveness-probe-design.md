# M837 V4 Near-Boundary Action-Effectiveness Probe Design

## Purpose

M837 designs the next no-training diagnostic after M836 audited M835 as an
all-weak wrong-history response/action intervention result.

The design question is:

```text
Are the M832 near-boundary states locally sensitive to bounded first-action
changes at all?
```

M837 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M832 fixed the boundary slack problem:

```text
accepted_boundary_rows: 39
boundary_margin_min: 0.0000494
boundary_margin_median: 0.009952
near_boundary_pair_rows: 60
```

M835 then showed that hidden and response/action counterfactuals create some
action drift but not outcome evidence:

```text
wrong_response_action_hidden max_action: 0.019600431767721204
wrong_action_history_hidden max_action:  0.017168803000693903
wrong_response_action_obs max_action:    0.014695116575514424

wrong_response_action_hidden max_gap: 0.00030215729621496656
wrong_response_action_obs max_gap:    0.0002744146905726552
zero_command_obs max_gap:             0.004670113250027308
primary_margin_gap_threshold:         0.01
accepted rows:                        0
```

This leaves an ambiguity:

```text
policy/history intervention is too weak
```

versus:

```text
the selected near-boundary states are not first-action controllable enough
```

M838 should resolve that ambiguity before any objective, architecture, PPO, or
promotion work.

## Actor Contract

The deployed actor and its input contract stay unchanged.

The probe may read logged policy actions and replay simulator states, but it
must not add deploy-time actor inputs:

```text
no hidden parameters
no fault labels
no oracle feasibility
no TTC
no path or reference errors
no slip or tire-force channels
no controller mode
```

Direct action overrides are offline diagnostics. They are not a policy, not a
reference generator, and not self-identification proof.

## Data Source

M838 should reuse the same source as M835:

```text
runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

No new source generation is part of M838.

The implementation should deduplicate reconstructed left-side snapshots from
the M832 pair rows, while preserving pair metadata for pair-delta directions.

## Replay Semantics

For each selected near-boundary pair `(left, right)`:

```text
env = relocated left environment
scene/context = left road and obstacle geometry
rollout dynamics = left fault/source dynamics
hidden = left policy hidden unless the baseline reconstruction requires it
normal action = current M568/M761 policy action at the left state
```

M838 applies a direct first-step override:

```text
action_override = clip_to_action_bounds(normal_action + delta)
```

After the first step, policy control resumes normally. This isolates whether
the current near-boundary state has local first-action leverage.

M838 should not use rolling wrong histories, policy retraining, or action
sequence execution. If first-step control is weak, that result should route to a
separate sequence-effectiveness or new-data design.

## Override Directions

M838 should evaluate fixed and pair-informed directions.

### Pair-Derived Directions

For each pair:

```text
d_pair = normalize(right_first_action - left_first_action)
```

Evaluate:

```text
pair_delta_positive
pair_delta_negative
```

This tests whether the action difference used by matching has any local outcome
effect when applied directly.

### Component Directions

Evaluate normalized axes:

```text
steer_positive
steer_negative
throttle_positive
throttle_negative
brake_positive
brake_negative
```

These are diagnostic axes, not rules. They test local simulator
controllability without assuming which direction should be correct.

### Optional Combined Directions

If the implementation can do this without adding branch complexity, it may log
combined directions separately:

```text
steer_positive_brake_positive
steer_negative_brake_positive
throttle_negative_brake_positive
```

These rows must not be required for the primary M838 result. They are only
diagnostics for whether single-axis perturbations understate action leverage.

## Override Bounds

Use a bounded L2 grid:

```text
epsilon_l2_grid: [0.014, 0.025, 0.05, 0.075]
max_override_l2: 0.075
```

The first value matches the M835 action-drift threshold. The largest value is
intended to be clearly visible while still small enough to remain a local probe.

Each action must be clipped to the actor action bounds before rollout. The
logged effective override must record:

```text
requested_delta_l2
effective_delta_l2_after_clip
action_before_clip
action_after_clip
clip_fraction
```

Rows with severe clipping should be retained but marked separately:

```text
clip_fraction > 0.25
```

They cannot be the only support for an action-effective claim.

## Metrics

For each override row, log:

```text
normal_success
normal_collision
normal_margin
override_success
override_collision
override_margin
margin_delta = override_margin - normal_margin
abs_margin_delta
degradation_margin_delta = normal_margin - override_margin
improvement_margin_delta = override_margin - normal_margin
success_flip
collision_flip
first_action_l2_vs_normal
direction
epsilon_l2
left/right candidate and source metadata
```

Use finite margins only for margin-delta gates. Collision and success flips are
recorded independently.

## Accepted Row Classes

### Primary Action-Effective Rows

Required:

```text
normal_collision == false
normal_margin <= 0.05
effective_delta_l2_after_clip >= 0.014
abs_margin_delta >= 0.01
or success_flip == true
or collision_flip == true
```

These rows prove only that the state is locally action-effective. They do not
prove the learned policy uses history correctly.

### Directional Degradation Rows

Rows where:

```text
degradation_margin_delta >= 0.01
or collision_flip_to_collision == true
```

These are useful for future counterfactual objectives because a bounded wrong
action can make the state worse.

### Directional Improvement Rows

Rows where:

```text
improvement_margin_delta >= 0.01
or collision_flip_to_success == true
```

These indicate that the current policy action is locally improvable, but they
are not self-ID proof and should not trigger PPO.

### Weak Rows

Rows with action movement but:

```text
abs_margin_delta < 0.01
and no success/collision flip
```

These support a first-action-insensitive result.

## Pass/Fail Interpretation

Strong action-effective diagnostic:

```text
accepted_primary_action_effective_rows >= 40
unique_left_sources >= 8
unique_fault_families >= 5
max_source_share <= 0.30
at least two direction families pass
```

Sparse positive diagnostic:

```text
10 <= accepted_primary_action_effective_rows < 40
and at least three fault families
```

All-weak result:

```text
accepted_primary_action_effective_rows < 10
and max_abs_margin_delta < 0.01
and no success/collision flips
```

If the result is all-weak, do not keep adding hidden/response intervention
variants on the same pair set. The next route should be:

```text
longer-horizon action sequence effectiveness
or new boundary-state mining with stronger local action leverage
```

If direct overrides are action-effective, the next route should be:

```text
outcome-coupled objective design
```

but only after an audit. Direct override evidence is a controllability
precondition, not a learned self-ID claim.

## Required M838 Artifacts

M838 should write:

```text
src/autodrift/v4_near_boundary_action_effectiveness_probe.py
tests/test_v4_near_boundary_action_effectiveness_probe.py
runs/m838_v4_near_boundary_action_effectiveness_probe/summary.json
runs/m838_v4_near_boundary_action_effectiveness_probe/action_effectiveness_rows.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/accepted_action_effective_rows.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/best_direction_by_pair.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/direction_summary.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/diversity_summary.json
runs/m838_v4_near_boundary_action_effectiveness_probe/rejected_rows.csv
docs/m838-v4-near-boundary-action-effectiveness-probe-implementation.md
```

The summary must include:

```text
result_class
selected_pair_rows
unique_snapshot_rows
action_effectiveness_rows
accepted_primary_action_effective_rows
accepted_directional_degradation_rows
accepted_directional_improvement_rows
max_abs_margin_delta
max_degradation_margin_delta
max_improvement_margin_delta
success_flip_rows
collision_flip_rows
actor_backbone_changed
residual_head_changed
training_started
optimizer_started
ppo_used
promoted
checkpoint_promoted
```

## Recommended M838 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_near_boundary_action_effectiveness_probe \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --near-boundary-pairs runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv \
  --accepted-boundary-rows runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m838_v4_near_boundary_action_effectiveness_probe \
  --device cpu
```

## Failure Taxonomy

Use:

```text
metric_artifact
```

if action movements exist but outcome margins do not move.

Use:

```text
scenario_sampling_failure
```

if the pair set is too sparse or the states are first-action-insensitive.

Use:

```text
contract_violation
```

only if the implementation changes actor inputs, trains parameters, or uses
hidden/oracle information as deployable actor input.

## Decision

Decision:

```text
near_boundary_action_effectiveness_probe_design_admit_m838
```

Next:

```text
m838-v4-near-boundary-action-effectiveness-probe-implementation
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, and threshold relaxation remain blocked.
