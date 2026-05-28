# M1270 Paper-Route Four-Wheel Source Viability Calibration Design

## Summary

M1270 designs the next bounded four-wheel source experiment after M1268/M1269.

Decision:

```text
four_wheel_source_viability_calibration_design_admit_smoke
```

Admit next bounded implementation:

```text
m1271-paper-route-four-wheel-source-viability-calibration-smoke
```

This is design-only. No training, PPO, checkpoint promotion, private holdout,
actor-input expansion, accepted-threshold relaxation, source-positive claim,
self-identification claim, paper-level claim, or high-fidelity validation claim
occurs in M1270.

## Blocker

M1268 changed the source blocker from low-regret to own-branch nonviability:

```text
accepted_separable_pairs: 0
best_actions_diverged_pairs: 27
low_regret_pairs: 92
own_branch_viability_fail_count: 103
all_four_rollouts_collision_count: 103
top min_cross_regret: 0.1793146044
```

The important signal is that four-wheel faults produced much stronger regret
than the previous source branch:

```text
M1262 max min_cross_regret: 0.0043813964
M1268 top min_cross_regret: 0.1793146044
```

But the original grid was too collision dominated to create accepted source
rows:

```text
terminal_reason collision: 2360
terminal_reason obstacle_completed: 16
terminal_reason safe_stop: 0
```

M1270 therefore changes the source-sampling grid rather than the acceptance
thresholds.

## Metric Guardrail

The M1268 metric artifact remains blocked:

```text
success = no collision and (obstacle_completed or safe_stop)
```

Horizon-only rows are not success.

The next smoke must keep this exact semantics and must report:

```text
accepted_separable_pairs
own_branch_viability_fail_count
all_four_rollouts_collision_count
terminal_reason histogram
accepted_fault_family_pairs
```

## Pre-Design Calibration Evidence

A bounded scratch sweep was run to select axes before writing this design. It
used the existing no-policy open-loop candidate lattice, unchanged thresholds,
and a calibrated scenario grid:

```text
speed: 14.0, 15.0, 16.0
obstacle_body_x: 12.0, 13.0, 14.0, 15.0, 16.0
obstacle_body_y: -0.25, 0.0, 0.25
obstacle_half_width: 0.55, 0.65, 0.75, 0.85
sequence_length: 72
fault pairs: 4
```

Scratch result:

```text
matched pairs: 720
accepted: 108
own-branch viable: 612
best actions diverged: 216
high-regret pairs: 159
own-branch viable and action-divergent: 150
```

Accepted rows were not source-collapsed to one family:

```text
single_wheel_brake_pull: 59
left_right_split_mu: 28
single_wheel_grip_collapse: 21
halfshaft_torque_loss: 0
```

Representative accepted high-regret rows:

```text
single_wheel_grip_collapse, speed=16, obstacle_x=15, y=0.0, half_width=0.65:
  best_action_l2=1.5
  min_cross_regret=0.5092
  own margins=0.4604 / 0.4604

left_right_split_mu, speed=16, obstacle_x=15, y=0.0, half_width=0.55:
  best_action_l2=1.5
  min_cross_regret=0.1112
  own margins=0.2320 / 0.2320
```

This scratch evidence is not a promotion result. It only justifies one official
bounded source-smoke with the calibrated grid.

## Scenario Profile

M1271 should add a named source scenario profile:

```text
scenario_profile: viability_calibration
```

The default M1268 profile must remain available:

```text
scenario_profile: m1268_default
```

The calibrated profile should use:

```text
speed: 14.0, 15.0, 16.0
obstacle_body_x: 12.0, 13.0, 14.0, 15.0, 16.0
obstacle_body_y: -0.25, 0.0, 0.25
obstacle_half_width: 0.55, 0.65, 0.75, 0.85
sequence_length: 72
dt: 0.02
brake_force: 6000.0
```

Rationale:

```text
lower speed and farther obstacle restore own-branch viability;
narrower half-width tests whether collision dominance was a geometry artifact;
center and slight lateral offsets preserve avoid-vs-avoid ambiguity;
established brake state preserves split-mu / brake-pull yaw-moment signal.
```

## Acceptance Contract

Keep strict source acceptance unchanged:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

Do not lower thresholds.

Do not count horizon-only rows.

Do not add per-wheel, fault, or search metadata to actor observations.

## Expected Artifacts

M1271 should write:

```text
runs/m1271_four_wheel_source_viability_calibration_smoke/summary.json
runs/m1271_four_wheel_source_viability_calibration_smoke/scenario_summary.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/snapshot_candidates.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/action_lattice.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/action_rollouts.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/matched_capability_pairs.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/accepted_separable_pairs.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/rejected_pairs.csv
runs/m1271_four_wheel_source_viability_calibration_smoke/model_fidelity_limits.md
```

Required summary guardrails:

```text
scenario_profile: viability_calibration
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Decision Rule

M1271 is allowed to claim source-smoke evidence only if artifacts exist and
guardrails hold.

If `accepted_separable_pairs > 0`, the next step is not training. The next step
is a result audit that checks:

```text
source diversity
terminal-reason distribution
family dominance
whether accepted rows are too easy / far from boundary
whether halfshaft remains inactive
whether the accepted rows are suitable for actor/history integration
```

If `accepted_separable_pairs == 0`, the next audit should decide whether the
four-wheel source branch still lacks action support, scenario support, or model
fidelity.

## Stop Conditions

Stop before running M1271 if any of these become necessary:

```text
actor input must include per-wheel/fault labels
accepted-source thresholds must be lowered
success must count horizon-only rows
the smoke requires PPO/training
```

Stop after M1271 and audit before continuing if:

```text
accepted rows all come from one family or one scenario
accepted rows are horizon-only or collision-adjacent artifacts
accepted rows are so easy that cross-history/history tests would not be useful
halfshaft is the only positive family or all non-halfshaft families vanish
```

## Next Step

Pre-register and run:

```text
experiments/manifests/m1271-paper-route-four-wheel-source-viability-calibration-smoke.json
```
