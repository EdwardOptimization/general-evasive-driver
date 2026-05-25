# M839 V4 Near-Boundary Action-Effectiveness Probe Audit

## Purpose

M839 audits M838 before any new implementation.

The audit question is:

```text
Is M838 a clean first-step action-effectiveness negative, and what is the next
highest-leverage no-training branch?
```

M839 is audit-only:

```text
no replay
no actor update
no M761 residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
runs/m838_v4_near_boundary_action_effectiveness_probe/summary.json
runs/m838_v4_near_boundary_action_effectiveness_probe/direction_summary.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/action_effectiveness_rows.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/best_direction_by_pair.csv
runs/m838_v4_near_boundary_action_effectiveness_probe/diversity_summary.json
docs/m838-v4-near-boundary-action-effectiveness-probe-implementation.md
```

M838 result class:

```text
v4_near_boundary_action_effectiveness_first_step_insensitive
```

## Artifact Consistency

M838 produced a complete no-training diagnostic:

```text
raw_pair_rows: 60
selected_pair_rows: 60
unique_snapshot_rows: 16
action_effectiveness_rows: 1920
rejected_rows: 0
```

The expected direction grid was complete:

```text
8 directions * 4 epsilon values * 60 pairs = 1920 rows
```

Every direction had `240` rows, no accepted rows, no success flips, no collision
flips, and no severe clipping. This is not an artifact-completeness failure.

## Contract Audit

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

The probe did not add hidden parameters, oracle labels, fault labels, TTC, path
errors, slip, tire force, or controller-mode inputs to the actor.

The direct action override is an offline diagnostic, not a deployed policy.

## Outcome Audit

Accepted rows:

```text
accepted_primary_action_effective_rows: 0
accepted_directional_degradation_rows: 0
accepted_directional_improvement_rows: 0
success_flip_rows: 0
collision_flip_rows: 0
```

Thresholds:

```text
action_l2_threshold: 0.014
margin_delta_threshold: 0.01
max_override_l2: 0.075
```

Largest observed margin changes:

```text
max_abs_margin_delta:         0.002649502705148077
max_degradation_margin_delta: 0.002649502705148077
max_improvement_margin_delta: 0.002591099447261991
```

M838 therefore moved the first action enough to be visible, but terminal margin
did not move enough to support a direct outcome-coupled first-step objective on
this corpus.

## Direction Audit

Best per-direction terminal-margin movement:

```text
throttle_positive:    0.002649502705148077
throttle_negative:    0.002591099447261991
pair_delta_negative:  0.0016304800420747778
pair_delta_positive:  0.0015691361193552744
steer_negative:       0.001527237539624915
steer_positive:       0.0013722334854635587
brake_negative:       0.0009930399851543203
brake_positive:       0.0009844319916982869
```

This matters because pair-delta directions were supposed to test the action
difference that made the M832 matched pairs action-divergent. Those pair
directions are also far below the `0.01` margin gate.

## Interpretation

M838 rules out a narrower hypothesis:

```text
M835 was weak only because policy/history interventions did not move the first
action enough.
```

Direct first-step action overrides move the first action by up to `0.075` L2
without producing accepted terminal-margin effects. This suggests the current
M832 near-boundary states are not first-step action-effective enough.

This is not a proof that the overall driver or self-ID direction is impossible.
It only says:

```text
the current M832 state surface is a weak first-step local-control surface
```

The likely reason is closed-loop recovery: after one forced action, the frozen
policy resumes and cancels much of the local perturbation. Another possibility
is that the selected terminal margin is dominated by later trajectory evolution
rather than the first action.

## Failure Taxonomy

### scenario_sampling_failure

Primary label. The M832 near-boundary pair set is near terminal boundary, but
not useful as a first-step action-effectiveness surface.

### metric_artifact

Secondary label. Large enough first-action movement is not sufficient evidence
when terminal margin and success/collision outcomes do not move.

### not contract_violation

Checksums stayed fixed and no forbidden actor inputs were introduced.

## Supported Claims

M838 supports:

- the direct first-action override probe is implemented and complete;
- M832 near-boundary states are first-step outcome-insensitive under bounded
  overrides up to `0.075` L2;
- pair-delta action differences are not locally outcome-effective on this
  first-step setup;
- continuing to add first-step hidden/response/action variants on this exact
  corpus is low leverage.

## Unsupported Claims

M838 does not support:

- learned response-history self-ID proof;
- a claim that the driver problem is impossible;
- a claim that action sequences are ineffective;
- a claim that fresh boundary-state mining would fail;
- PPO admission;
- checkpoint promotion.

## Next Control Variable

The next question should be:

```text
Does bounded short-horizon action-sequence intervention move terminal margin on
the same near-boundary states?
```

This is the direct follow-up because M838 only forced the first action and then
returned control to the policy. A short-horizon sequence probe can test whether
terminal margin is sensitive to sustained maneuver intent over several steps.

M840 should design a no-training sequence-effectiveness probe:

```text
hold_steps: [2, 4, 6]
directions: pair_delta, steer, throttle, brake
epsilon_l2_grid: [0.014, 0.025, 0.05, 0.075]
execute: bounded action delta for hold_steps, then resume policy
```

Interpretation rules:

```text
positive sequence-effectiveness -> design outcome-coupled sequence objective
all-weak sequence-effectiveness -> pivot to fresh action-leverage boundary mining
```

Direct sequence override evidence still must not be treated as learned policy
self-ID proof. It is only a controllability precondition.

## Decision

Decision:

```text
admit_short_horizon_sequence_effectiveness_probe_design
```

Next:

```text
m840-v4-near-boundary-sequence-effectiveness-probe-design
```

PPO, checkpoint promotion, actor training, residual-head training, learned
gating, outcome-coupled objective training, and threshold relaxation remain
blocked.
