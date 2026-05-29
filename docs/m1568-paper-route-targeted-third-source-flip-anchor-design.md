# M1568 Paper-Route Targeted Third-Source Flip-Anchor Design

## Summary

M1568 designs the final targeted repair admitted by M1567.

Decision:

```text
targeted_third_source_flip_anchor_design_admit_bounded_implementation
```

M1566 produced many recoverable and strong recoverable anchors, but flip anchors
still came from only two source families. M1567 found that two other families
already have strong active-set mass:

```text
t5_high_speed_close_obstacle
late_reveal_boundary
```

M1568 therefore targets those families explicitly. It does not run simulator
traces, history interventions, materialization, training, PPO, private holdout,
promotion, or any self-identification claim.

Workflow cadence is now due. This design is recorded as the proposed next
implementation, but the next milestone must be branch synthesis before any
implementation smoke.

## Evidence From M1566

High-speed recoverable anchors:

```text
t5_high_speed_close_obstacle recoverable: 29
t5_high_speed_close_obstacle strong: 13
normal collision anchors: 17
normal success anchors: 12
windows: decision_minus_24, decision_minus_16, reveal, reveal_plus_4
```

Late-reveal recoverable anchors:

```text
late_reveal_boundary recoverable: 18
late_reveal_boundary strong: 10
normal collision anchors: 18
normal success anchors: 0
windows: decision_minus_24, decision_minus_16, reveal
```

Both families have enough active-set mass to justify one targeted repair. The
problem is not absence of near-boundary rows; it is that the current task
retargeting and local holds do not push those rows across the terminal outcome
boundary.

## Targeted Repair Scope

The next implementation, if admitted by synthesis, should run one bounded public
source-generation repair focused on:

```text
target families:
  t5_high_speed_close_obstacle
  late_reveal_boundary

diagnostic bonus only:
  curved_boundary_obstacle
```

The existing flip families remain in the run for comparison:

```text
t5_boundary_axis_retarget
t5_near_boundary_warmup
```

But the implementation must not pass by only improving those existing two
families. It must report third-source flip evidence separately.

## Source-Generation Changes

The implementation may reuse the M1566 repair runner and add a targeted
source-spec expansion before anchor generation.

For `t5_high_speed_close_obstacle`, emphasize:

```text
closer obstacle distance scale;
wider obstacle half-width;
slightly higher speed;
decision_minus_24 / decision_minus_16 / reveal windows;
normal-success small-positive margin rows;
normal-collision small-negative margin rows;
```

For `late_reveal_boundary`, emphasize:

```text
late reveal but collision-sensitive predecision windows;
obstacle distance slightly less aggressive than M1566 when rows are already
deep collision;
wider obstacle half-width only when normal margins are near zero;
steering/brake authority combinations that preserve P0 observations;
decision_minus_24 and decision_minus_16 windows.
```

Curved-boundary rows can be included only as diagnostic bonus because M1566
found just two recoverable curved anchors.

## Local-Hold Probes

The implementation should keep all M1566 probes and may add a small
pre-registered targeted set:

```text
steer_left_full_brake_long
steer_right_full_brake_long
brake_pulse_then_release
steer_left_brake_release
steer_right_brake_release
```

These probes are still diagnostics only. They are not a controller, not an actor
output change, and not a training target.

## Proposed Implementation Public Gates

The targeted implementation should pass only if all guardrails are clean and
these minimums hold:

```text
source_spec_count >= 300
anchor_candidate_count >= 320
replay_ok_anchor_count >= 160
recoverable_boundary_anchor_count >= 48
strong_recoverable_boundary_anchor_count >= 16
active_source_family_count >= 5
active_window_count >= 5
distinct_collision_flip_anchor_count >= 8
distinct_success_flip_anchor_count >= 8
flip_anchor_source_family_count >= 3
third_source_flip_anchor_count >= 1
targeted_family_flip_anchor_count >= 1
flip_anchor_window_count >= 3
max_single_flip_source_family_share <= 0.60
guardrail_violation_count == 0
history_interventions_executed == false
candidate_materialized == false
training_corpus_exported == false
```

Definitions:

```text
third_source_flip_anchor_count:
  flip anchors from source families other than
  t5_boundary_axis_retarget and t5_near_boundary_warmup

targeted_family_flip_anchor_count:
  flip anchors from t5_high_speed_close_obstacle or late_reveal_boundary
```

Evidence-quality targets:

```text
distinct_collision_flip_anchor_count >= 10
distinct_success_flip_anchor_count >= 10
flip_anchor_source_family_count >= 3
third_source_flip_anchor_count >= 3
targeted_family_flip_anchor_count >= 3
max_single_flip_source_family_share <= 0.50
```

## Hard Stop

The targeted implementation is the final implementation attempt in this
recoverable active-set repair sub-branch.

If the targeted implementation still has:

```text
flip_anchor_source_family_count < 3
```

then the following milestone must be branch synthesis, not another targeted
generator implementation.

If the targeted implementation passes public gates, the following milestone is
still an audit, not history-intervention design.

Before that implementation, the immediate next milestone is a mandatory branch
synthesis:

```text
m1569-paper-route-recoverable-active-set-generation-branch-synthesis
```

## Required Artifacts

The targeted implementation should write:

```text
runs/m1569_targeted_third_source_flip_anchor_smoke/source_spec_rows.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/anchor_candidate_rows.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/local_hold_rows.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/recoverable_active_anchor_rows.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/flip_anchor_rows.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/targeted_flip_anchor_rows.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/source_family_summary.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/flip_source_summary.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/guardrail_summary.csv
runs/m1569_targeted_third_source_flip_anchor_smoke/summary.json
```

Do not write:

```text
history intervention rows;
training corpus;
checkpoint;
promotion artifact.
```

## Guardrails

```text
history_interventions_executed: false in M1568
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
m1569-paper-route-recoverable-active-set-generation-branch-synthesis
```
