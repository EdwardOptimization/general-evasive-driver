# M840 V4 Near-Boundary Sequence-Effectiveness Probe Design

## Purpose

M840 designs the next no-training diagnostic after M839 audited M838 as a clean
first-step action-effectiveness negative.

The design question is:

```text
Are the M832 near-boundary states sensitive to bounded short-horizon action
sequence interventions even though one-step overrides are weak?
```

M840 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M838 applied direct first-step overrides and then returned control to the frozen
policy:

```text
selected_pair_rows: 60
action_effectiveness_rows: 1920
accepted_primary_action_effective_rows: 0
success_flip_rows: 0
collision_flip_rows: 0
max_abs_margin_delta: 0.002649502705148077
margin_delta_threshold: 0.01
```

This shows the M832 states are not useful first-step action-effectiveness
surfaces. But it does not show that short-horizon maneuvers are ineffective.
The closed-loop policy may simply cancel a one-step override.

M841 should therefore test sustained action intent over a short horizon before
we abandon this data route or design objectives.

## Actor Contract

The deployed actor and P0 human-view observation contract remain unchanged.

The sequence override is an offline simulator intervention:

```text
action_t = clip(policy_action_t + delta_direction * epsilon)
```

for a fixed number of initial steps, then normal policy control resumes.

This direct sequence override must not be treated as learned policy self-ID
proof. It only tests whether the current state surface is controllable by a
short bounded action sequence.

Forbidden shortcuts remain forbidden:

```text
no hidden parameters as actor input
no fault labels as actor input
no oracle feasibility
no TTC or path reference errors
no slip or tire-force actor channels
no controller mode
no training
```

## Data Source

M841 should reuse:

```text
runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv
runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/direction_summary.csv
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

No new source generation belongs in M841.

## Sequence Override Semantics

For each pair `(left, right)`:

```text
env = relocated left environment
scene/context = left road and obstacle geometry
rollout dynamics = left fault/source dynamics
hidden = left recurrent hidden
```

At every intervention step `t < hold_steps`:

```text
policy_action_t = frozen_policy(obs_t, hidden_t)
override_action_t = clip(policy_action_t + direction_unit * epsilon)
execute override_action_t
update hidden normally from obs_t
```

After `hold_steps`, execute the normal frozen policy.

This is not open-loop fixed-action replay. It is a bounded delta around the
policy's own current action for several steps. That keeps the probe local while
testing sustained maneuver intent.

## Hold Steps

Use:

```text
hold_steps_grid: [2, 4, 6]
```

Interpretation:

```text
2 steps: minimal sustained intent
4 steps: short maneuver pulse
6 steps: roughly one M832 horizon when left_plan horizon is unavailable
```

Each hold-step result must be logged separately. Do not pool one-step and
sequence rows into the same claim; M838 already covers the one-step case.

## Directions

Use the same direction families as M838:

```text
pair_delta_positive
pair_delta_negative
steer_positive
steer_negative
throttle_positive
throttle_negative
brake_positive
brake_negative
```

Pair delta remains:

```text
normalize(right_first_action - left_first_action)
```

and is fixed across the sequence.

## Bounds

Use the same per-step L2 grid:

```text
epsilon_l2_grid: [0.014, 0.025, 0.05, 0.075]
max_per_step_override_l2: 0.075
```

Log:

```text
hold_steps
requested_delta_l2_per_step
effective_delta_l2_mean
effective_delta_l2_max
effective_sequence_l2
clip_fraction_mean
clip_fraction_max
severe_clip_steps
```

Rows with severe clipping can be diagnostics, but they cannot be the only
support for a sequence-effective claim.

## Metrics

For each sequence override row, log:

```text
normal_success
normal_collision
normal_margin
sequence_success
sequence_collision
sequence_margin
margin_delta = sequence_margin - normal_margin
abs_margin_delta
degradation_margin_delta
improvement_margin_delta
success_flip
collision_flip
prefix_l2_mean_vs_normal
prefix_l2_max_vs_normal
effective_sequence_l2
hold_steps
direction
epsilon_l2
```

Use finite terminal margins for margin-delta gates. Success and collision flips
are independent outcome gates.

## Accepted Row Classes

### Primary Sequence-Effective Rows

Required:

```text
normal_collision == false
normal_margin <= 0.05
effective_delta_l2_mean >= 0.014
abs_margin_delta >= 0.01
or success_flip == true
or collision_flip == true
```

### Directional Degradation Rows

Rows where the sequence makes the outcome worse:

```text
degradation_margin_delta >= 0.01
or collision_flip_to_collision == true
```

### Directional Improvement Rows

Rows where the sequence improves the outcome:

```text
improvement_margin_delta >= 0.01
or collision_flip_to_success == true
```

### Hold-Step Diagnostics

Summarize accepted rows by:

```text
hold_steps
direction
direction_family
epsilon_l2
```

If only `hold_steps=6` passes and shorter holds fail, the corpus may require
sequence-level objectives rather than one-step action objectives.

## Pass/Fail Interpretation

Strong sequence-effective diagnostic:

```text
accepted_primary_sequence_effective_rows >= 40
unique_left_sources >= 8
unique_fault_families >= 5
max_source_share <= 0.30
at least two direction families pass
at least two hold_steps values pass
```

Sparse positive diagnostic:

```text
10 <= accepted_primary_sequence_effective_rows < 40
and at least three fault families
```

All-weak result:

```text
accepted_primary_sequence_effective_rows < 10
and max_abs_margin_delta < 0.01
and no success/collision flips
```

If sequence overrides are positive, the next branch can design an
outcome-coupled sequence objective. If sequence overrides are also all-weak,
the branch should pivot to fresh boundary-state mining focused on local action
leverage instead of continuing to tune interventions on M832.

## Required M841 Artifacts

M841 should write:

```text
src/autodrift/v4_near_boundary_sequence_effectiveness_probe.py
tests/test_v4_near_boundary_sequence_effectiveness_probe.py
runs/m841_v4_near_boundary_sequence_effectiveness_probe/summary.json
runs/m841_v4_near_boundary_sequence_effectiveness_probe/sequence_effectiveness_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/accepted_sequence_effective_rows.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/best_sequence_by_pair.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/direction_hold_summary.csv
runs/m841_v4_near_boundary_sequence_effectiveness_probe/diversity_summary.json
runs/m841_v4_near_boundary_sequence_effectiveness_probe/rejected_rows.csv
docs/m841-v4-near-boundary-sequence-effectiveness-probe-implementation.md
```

The summary must include:

```text
result_class
selected_pair_rows
unique_snapshot_rows
sequence_effectiveness_rows
accepted_primary_sequence_effective_rows
accepted_directional_degradation_rows
accepted_directional_improvement_rows
success_flip_rows
collision_flip_rows
max_abs_margin_delta
max_degradation_margin_delta
max_improvement_margin_delta
actor_backbone_changed
residual_head_changed
training_started
optimizer_started
ppo_used
promoted
checkpoint_promoted
```

## Recommended M841 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_near_boundary_sequence_effectiveness_probe \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --near-boundary-pairs runs/m832_v4_near_boundary_wrong_history_pair_mining/near_boundary_pair_rows.csv \
  --accepted-boundary-rows runs/m832_v4_near_boundary_wrong_history_pair_mining/accepted_boundary_rows.csv \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --candidate-plan-rows runs/m825_v4_extreme_hidden_dynamics_data_route/candidate_plan_rows.csv \
  --run-dir runs/m841_v4_near_boundary_sequence_effectiveness_probe \
  --device cpu
```

## Failure Taxonomy

Use:

```text
metric_artifact
```

if action sequence movement exists but terminal margins do not move.

Use:

```text
scenario_sampling_failure
```

if the M832 state surface is weak even under short-horizon bounded sequences.

Use:

```text
contract_violation
```

only if the implementation changes actor inputs, trains parameters, or uses
hidden/oracle fields as deployable actor input.

## Workflow Note

M841 will be the tenth non-synthesis milestone after M831. If M841 completes,
the next step should be a branch synthesis before more narrow implementation
work.

## Decision

Decision:

```text
near_boundary_sequence_effectiveness_probe_design_admit_m841
```

Next:

```text
m841-v4-near-boundary-sequence-effectiveness-probe-implementation
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, outcome-coupled objective training, and threshold relaxation remain
blocked.
