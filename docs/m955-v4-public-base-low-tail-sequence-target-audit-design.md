# M955 V4 Public Base Low-Tail Sequence Target Audit Design

## Purpose

M955 designs the next no-training audit after M954.

It does not train, run PPO, update model weights, change actor inputs, use
private holdout, or promote.

M954 showed:

```text
M267/M264 target preflight is mostly solved.
One-step exact low-tail target feasibility is not solved.
```

Therefore M955 should not repeat more one-step projection sweeps. It should
design a short-horizon sequence target audit to test whether the exact
one-step low-tail gate is under-specified for the behavior we actually need.

## M954 Evidence To Preserve

M954 result:

```text
offline_target_family_count: 56
m267_target_preflight_family_count: 56
m267_target_preflight_pass_count: 55
exact_target_candidate_count: 0
joint_feasible_target_count: 0
normal_safe_low_tail_trend_count: 27
result_class: replay_constrained_target_feasibility_low_tail_exact_failure
```

The active boundary:

```text
best normal-retained one-step family:
  existing_m951_alpha_0_0500
  normal_retention_pass: true
  tail_lift_pass: false
  m267_target_preflight_pass: true

smallest one-step projection tail-lift family:
  projection_gap_scale_0_75_drift_0_0060
  normal_retention_pass: false
  tail_lift_pass: true
  m267_target_preflight_pass: true
```

This suggests the first action alone cannot carry enough low-tail movement
under the registered first-action retention thresholds. The next variable is
time: keep the first action inside retention, then distribute the maneuver over
a short prefix.

## Audit Question

M956 should answer:

```text
Can short-horizon target sequences improve low-tail closed-loop behavior while
keeping first-action normal retention and M267/M264 wrong-history proof?
```

This is not an actor architecture change. It is a no-training target-space
feasibility audit.

## Sequence Target Contract

The deployed actor remains single-step:

```text
action_t = [steer, throttle, brake]
```

M956 may construct diagnostic target sequences:

```text
u_0, u_1, ..., u_{K-1}
K in {2, 4, 6}
```

The sequence is only used for no-training replay/target feasibility. It is not
an actor output contract change and does not authorize `action_sequence_horizon
> 1` for the online recurrent mainline actor.

## Candidate Families

### Family A: Retained-First-Action Sequence Projection

Keep `u_0` inside M954 normal retention and distribute the low-tail movement to
later prefix steps:

```text
u_0 = M399 or M951 alpha 0.0500 first action
u_1..u_{K-1} = projected action deltas away from intervention sequence
```

This directly tests whether the one-step exact gate fails because all movement
was forced into the first action.

### Family B: Delayed Projection Sequence

Use the same low-tail projection direction as M954, but delay the largest
action movement:

```text
u_0: drift budget <= M954 normal-retained budget
u_1/u_2: larger projection budget
u_3..: decay back toward policy action
```

This is useful if emergency response needs a small setup action followed by a
larger yaw/brake action after actuator and tire response starts to appear.

### Family C: Existing Direction Prefix

Use existing M951 alpha directions as a prefix baseline:

```text
alpha 0.0500: normal retained, not tail lift
alpha 0.0675+: tail lift, not normal retained
```

Construct a prefix schedule:

```text
step 0: alpha 0.0500
step 1..K-1: alpha 0.0675 or 0.0750 direction
```

This asks whether the same direction becomes feasible if it is delayed rather
than applied entirely at step 0.

### Family D: Branch-Separated M267 Proof Sequence

For M267/M264 rows `6`, `13`, `15`, and `16`, use separate normal/wrong-history
prefix targets:

```text
normal branch:
  base normal or normal-success prefix

wrong-history branch:
  base wrong-history or wrong-failure-preserving prefix
```

The target must not repair wrong-history into the normal safe maneuver. This is
the self-identification proof condition.

## Metrics

M956 should separate first-action retention from sequence-level effect.

### First-Action Retention Gate

The first action must still satisfy M954-style retention:

```text
normal_anchor_mse_mean <= 0.000004
normal_anchor_mse_p95 <= 0.000025
first_action_drift_from_base_mean <= 0.003
first_action_drift_from_base_p95 <= 0.008
```

If this fails, the sequence target is not solving M954; it is just hiding the
same one-step violation in a new artifact.

### Prefix Retention Gate

For horizon `K`, report:

```text
prefix_l2_mean
prefix_l2_p95
prefix_l2_max
prefix_action_mse_mean
prefix_action_mse_p95
```

Initial thresholds should be diagnostic, not promotive:

```text
K=2: prefix_l2_mean <= 0.006
K=4: prefix_l2_mean <= 0.010
K=6: prefix_l2_mean <= 0.014
```

These thresholds are not promotion criteria. They are used to sort feasible
sequence targets by how much extra maneuver intent they require.

### Sequence Low-Tail Gate

The one-step `tail_lift_pass` metric should not be reused as the only success
criterion. M956 should add sequence-level metrics:

```text
normal_vs_intervention_prefix_gap_p10
prefix_gap_deficit_mean
low_tail_prefix_fraction
low_tail_terminal_margin_mean_delta
low_tail_terminal_collision_delta
low_tail_terminal_success_delta
```

Candidate sequence target passes the sequence low-tail gate if:

```text
first-action retention: pass
prefix_gap_deficit_mean improves versus M954 best normal-retained family
low_tail_prefix_fraction improves versus M954 best normal-retained family
terminal margin does not regress
collision/success does not regress
```

If sequence prefix metrics improve but terminal margin does not, classify the
result as target-metric artifact rather than a candidate.

### M267 Proof-Retention Gate

M267/M264 active rows remain mandatory:

```text
rows: 6, 13, 15, 16
normal branch: success
wrong-history branch: failure
success_drop_count: 17 / 17 when full M267/M264 preflight is used
normal_margin_mean_delta >= -0.005
margin_gap_mean_delta >= -0.001
```

This gate should be evaluated with branch-separated sequence overrides, not a
single shared sequence.

## Required Artifacts For M956

M956 should write:

```text
runs/m956_v4_public_base_low_tail_sequence_target_audit/summary.json
runs/m956_v4_public_base_low_tail_sequence_target_audit/sequence_family_summary.csv
runs/m956_v4_public_base_low_tail_sequence_target_audit/low_tail_sequence_metrics.csv
runs/m956_v4_public_base_low_tail_sequence_target_audit/m267_sequence_preflight.csv
runs/m956_v4_public_base_low_tail_sequence_target_audit/sequence_row_conflicts.csv
```

The summary must include:

```text
training_started: false
ppo_used: false
promoted: false
actor_input_contract_changed: false
sequence_family_count
first_action_retained_family_count
sequence_low_tail_candidate_count
m267_sequence_preflight_pass_count
joint_sequence_candidate_count
result_class
next_blocker
```

## Route Logic

If `joint_sequence_candidate_count > 0`:

```text
route: sequence target export and actor-fit objective design
```

This would mean one-step exact target feasibility was under-specified, and the
next problem is fitting the sequence-induced target behavior without changing
the deployed single-step actor contract.

If sequence candidates improve prefix metrics but terminal margins do not:

```text
route: target-metric artifact audit
```

This means the sequence metric is not behaviorally grounded enough.

If first-action retention passes but no sequence low-tail candidate appears:

```text
route: exact threshold sensitivity audit
```

This would mean the current low-tail threshold may be too tight for any
normal-retained short-prefix action target.

If M267 proof fails while sequence low-tail passes:

```text
route: branch-separated sequence target refinement
```

This means the wrong-history branch is again being repaired into safety.

If no sequence family can be evaluated:

```text
route: sequence replay infrastructure repair
```

## Decision For Next Milestone

M955 routes to:

```text
m956-v4-public-base-low-tail-sequence-target-audit-implementation
```

M956 should implement the no-training sequence target audit. It must not train,
run PPO, change actor inputs, or promote.
