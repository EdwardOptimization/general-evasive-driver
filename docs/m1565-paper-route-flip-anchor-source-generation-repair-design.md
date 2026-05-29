# M1565 Paper-Route Flip-Anchor Source-Generation Repair Design

## Summary

M1565 designs the next bounded repair after M1564.

Decision:

```text
flip_anchor_source_generation_repair_design_admit_bounded_generator
```

M1563 proved that a source/window-balanced selector can be built from M1560
artifacts. M1564 showed that the remaining blocker is not selector balance but
distinct flip-anchor shortage:

```text
selected_collision_flip_anchor_count: 5
selected_success_flip_anchor_count: 5
flip_anchor_source_family_count: 1
required distinct collision/success flip anchors: 8 each
```

M1565 therefore designs a source-generation repair. It does not run the
simulator, history interventions, materialization, training, PPO, private
holdout, or promotion.

## Core Change

The next implementation should target distinct flip anchors directly:

```text
source-diverse recoverable anchors where bounded local holds flip success or
collision.
```

The repair should not treat repeated local-hold variants on the same anchor as
independent anchors. Variant counts remain diagnostic, but the gate should be
based on distinct anchor IDs and source/window diversity.

## Inputs

M1566 may reuse public artifacts and code paths from:

```text
docs/m1559-paper-route-recoverable-active-set-generation-design.md
runs/m1560_recoverable_active_set_generator_smoke/summary.json
runs/m1563_source_balanced_recoverable_active_set_selector/summary.json
src/autodrift/recoverable_active_set_generator.py
```

The active checkpoint remains:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Actor input contract remains P0 human-view/no-privileged. Hidden simulator
conditions may be randomized or paired for source generation, but they must not
enter actor observations.

## Repair Strategy

M1566 should extend the recoverable active-set generator with a flip-anchor
targeting mode.

Source families should include at least:

```text
t5_boundary_axis_retarget
t5_near_boundary_warmup
t5_high_speed_close_obstacle
late_reveal_boundary
curved_boundary_obstacle
```

The repair should bias source generation toward conditions where local control
can change the terminal outcome:

```text
normal terminal margin near zero;
normal collision with recoverable slack;
normal success with small positive clearance;
obstacle distance/width/lateral offset retargeted around the actor boundary;
decision and predecision anchors before the outcome is fixed;
speed/friction/actuator-lag combinations that produce different yaw/brake
authority but remain valid P0 observations.
```

Local-hold search should remain bounded and diagnostic. It may add a small set
of stronger but still actuator-level local holds if pre-registered:

```text
hold_steps: 1, 4, 8, 12, 16
steer_left
steer_right
brake_more
brake_less
throttle_release
steer_left_brake_more
steer_right_brake_more
steer_left_brake_less
steer_right_brake_less
full_brake_release_throttle
steer_left_full_brake
steer_right_full_brake
```

These are not a controller and not a training target. They are only local
diagnostics for whether an anchor is on an outcome boundary.

## Candidate Selection

M1566 should keep the M1560 triage labels:

```text
already_colliding
high_margin_safe
inactive_boundary
recoverable_boundary
strong_recoverable_boundary
```

It should add flip-anchor diagnostics:

```text
collision_flip_anchor
success_flip_anchor
both_flip_anchor
flip_anchor_source_family
flip_anchor_window
flip_anchor_variant_count
```

Ranking for the repaired output should prioritize:

```text
distinct anchors with collision or success flips;
source families that are not t5_boundary_axis_retarget;
windows not already saturated by decision_minus_24 / decision_minus_16;
strong recoverable anchors;
normal margins near zero but not already unrecoverable;
predecision anchors over final decision anchors.
```

## M1566 Public Gates

M1566 should pass only if all guardrails are clean and these minimums hold:

```text
source_spec_count >= 200
anchor_candidate_count >= 300
replay_ok_anchor_count >= 160
recoverable_boundary_anchor_count >= 48
strong_recoverable_boundary_anchor_count >= 16
predecision_recoverable_anchor_count >= 24
active_source_family_count >= 5
active_window_count >= 5
max_single_active_family_share <= 0.40
distinct_collision_flip_anchor_count >= 8
distinct_success_flip_anchor_count >= 8
flip_anchor_source_family_count >= 3
flip_anchor_window_count >= 3
max_single_flip_source_family_share <= 0.60
guardrail_violation_count == 0
history_interventions_executed == false
training_corpus_exported == false
candidate_materialized == false
```

Evidence-quality targets:

```text
distinct_collision_flip_anchor_count >= 12
distinct_success_flip_anchor_count >= 12
flip_anchor_source_family_count >= 4
flip_anchor_window_count >= 4
max_single_flip_source_family_share <= 0.45
selected_recoverable_anchor_count >= 40
selected_strong_recoverable_anchor_count >= 24
selected_source_family_count >= 5
selected_window_count >= 5
```

The evidence-quality targets decide whether the branch may later admit
history-intervention design. They do not promote any checkpoint.

## Required Artifacts

M1566 should write:

```text
runs/m1566_flip_anchor_source_generation_repair_smoke/source_spec_rows.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/anchor_candidate_rows.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/local_hold_rows.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/recoverable_active_anchor_rows.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/flip_anchor_rows.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/source_family_summary.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/window_summary.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/flip_source_summary.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/guardrail_summary.csv
runs/m1566_flip_anchor_source_generation_repair_smoke/summary.json
```

Do not write:

```text
history intervention rows;
training corpus;
checkpoint;
promotion artifact.
```

## Follow-Up Logic

If M1566 passes:

```text
M1567 audits the repaired flip-anchor distribution.
Only after that audit may a later milestone design history interventions over
the repaired active set.
```

If M1566 fails:

```text
M1567 audits whether the current simulator/task families cannot produce
source-diverse distinct flip anchors, whether source generation needs a broader
task-family expansion, or whether this recoverable active-set branch should
synthesize and pivot.
```

## Guardrails

```text
history_interventions_executed: false in M1565
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1566-paper-route-flip-anchor-source-generation-repair-implementation
```
