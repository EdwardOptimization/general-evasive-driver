# M959 V4 Public Base Low-Tail Direction-Family Target Audit Design

## Purpose

M959 designs the next no-training audit after M958.

It does not train, update model weights, run PPO, change actor inputs, relax
thresholds, use private holdout, or promote.

M958 found a direction-sign suspicion:

```text
away_from_intervention:
  proxy_improved_fraction: 1.000000
  behavior_improved_fraction: 0.000000
  terminal_margin_mean_delta: -0.000057

toward_intervention:
  proxy_improved_fraction: 0.000000
  behavior_improved_fraction: 1.000000
  terminal_margin_mean_delta: +0.000057
```

The old low-tail target construction moved away from the intervention action.
That improves the action-gap proxy, but it worsens closed-loop terminal margin
on the sampled rows. The next question is therefore narrower and more useful:

```text
Can behavior-improving direction families from M958 be converted into
normal-retained, proof-retained target candidates before actor training?
```

## Evidence From M958

M958 evaluated `10` direction families over `64` low-tail rows and `1920`
row/action cases.

Behavior-improving families:

```text
throttle_minus:
  behavior_improved_fraction: 1.000000
  terminal_margin_mean_delta: +0.000069
  terminal_margin_p10_delta: +0.000033

brake_plus:
  behavior_improved_fraction: 1.000000
  terminal_margin_mean_delta: +0.000047
  terminal_margin_p10_delta: +0.000024

toward_intervention:
  behavior_improved_fraction: 1.000000
  terminal_margin_mean_delta: +0.000057
  terminal_margin_p10_delta: +0.000025

steer_minus_brake_plus:
  behavior_improved_fraction: 1.000000
  terminal_margin_mean_delta: +0.000046
  terminal_margin_p10_delta: +0.000026

steer_minus:
  behavior_improved_fraction: 0.828125
  terminal_margin_mean_delta: +0.000018

steer_plus_brake_plus:
  behavior_improved_fraction: 0.812500
  terminal_margin_mean_delta: +0.000020
```

Anti-aligned families:

```text
away_from_intervention
throttle_plus
brake_minus
steer_plus
```

These may remain diagnostic rows, but they must not be the primary target
source for the next actor-fitting route.

## Audit Question

M960 should answer:

```text
After applying normal-retention and M267/M264 proof-retention checks, which
behavior-improving direction families are still valid target candidates?
```

This is not yet an actor-fitting experiment. It is a target-space admissibility
audit.

## Candidate Direction Families

M960 should start from M958's closed-loop behavior evidence and split families
into three groups.

### Primary Target Families

These are behavior-improving and have positive low-tail terminal-margin trend:

```text
throttle_minus
brake_plus
toward_intervention
steer_minus_brake_plus
```

They should be evaluated at small amplitudes:

```text
0.001, 0.002, 0.004, 0.006, 0.008
```

The lower amplitudes are important because M954-M956 repeatedly showed a narrow
normal-retention boundary.

### Secondary Target Families

These are partly behavior-improving, but have weaker or mixed tail behavior:

```text
steer_minus
steer_plus_brake_plus
```

They should only be considered after the primary families are evaluated, and
only if their row-level behavior passes retention checks.

### Diagnostic-Only Families

These should be evaluated only to confirm the sign diagnosis:

```text
away_from_intervention
throttle_plus
brake_minus
steer_plus
```

They must not be exported as training targets unless M960 finds a row-specific
exception with positive terminal-margin evidence.

## Target Construction

For every low-tail row and candidate family, M960 should construct a proposed
normal-history target action:

```text
target_action = clamp(base_normal_action + amplitude * unit_direction)
```

For `toward_intervention`:

```text
unit_direction = normalize(intervention_action - base_normal_action)
```

For action-axis families:

```text
steer_minus:              [-1,  0,  0]
brake_plus:               [ 0,  0, +1]
throttle_minus:           [ 0, -1,  0]
steer_minus_brake_plus:   normalize([-1, 0, +1])
steer_plus_brake_plus:    normalize([+1, 0, +1])
```

The action order remains the existing actor output order:

```text
steer, throttle, brake
```

Throttle and brake remain independent continuous outputs. M960 must not add a
new output command, reference trajectory, mode label, or throttle/brake
exclusivity rule.

## Required Checks

M960 should keep four checks separate.

### 1. Normal Retention

A target family is normal-retained only if it stays inside the target-space
trust region used by M953/M954:

```text
first_action_drift_from_base_mean <= 0.003
normal_anchor_mse_mean <= 0.000004
normal_anchor_mse_p95 does not exceed the registered row-level bound
no action bound clipping dominates the family
```

The exact implementation may report additional row-level retention statistics,
but the route decision must include both mean and tail retention.

### 2. Closed-Loop Behavior Grounding

A target family is behavior-grounded only if the direction remains positive
after aggregation:

```text
terminal_margin_mean_delta > 0
terminal_margin_p10_delta >= 0 for primary acceptance
positive_margin_fraction >= 0.80
success_delta >= 0
collision_delta <= 0
```

If a family improves mean margin but has negative p10 margin, it may be
reported as a trend, not as a primary target candidate.

### 3. Low-Tail Target Metric Compatibility

M960 should still report the existing low-tail proxy metrics, but they are not
allowed to override terminal-margin evidence:

```text
normal_intervention_gap_delta
gap_deficit_delta
low_tail_proxy_improved
low_tail_fraction
target_action_mse_mean
strict_target_action_mse_mean
```

If a behavior-improving family worsens the old proxy, M960 should classify that
as `proxy_anti_aligned_but_behavior_grounded`, not as an automatic rejection.

### 4. M267/M264 Proof Retention

M960 must run a branch-separated target preflight for active M267/M264 rows:

```text
rows: 6, 13, 15, 16
normal-history branch: target must not break normal success
wrong-history branch: target must not make wrong-history rollout safe
success_drop_count should remain 17 / 17 for full acceptance
```

If only the low-tail normal branch changes, wrong-history targets should stay
anchored to the base wrong-history action or to the previously accepted
wrong-failure-preserving target. The audit must not push wrong-history actions
toward the normal safe branch.

## Required Artifacts For M960

M960 should write:

```text
runs/m960_v4_public_base_low_tail_direction_family_target_audit/summary.json
runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_family_summary.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/direction_target_rows.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/normal_retention_metrics.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/m267_direction_target_preflight.csv
runs/m960_v4_public_base_low_tail_direction_family_target_audit/route_decision.csv
```

The summary must include:

```text
training_started: false
ppo_used: false
promoted: false
actor_input_contract_changed: false
evaluated_low_tail_rows
direction_family_count
primary_family_count
normal_retained_family_count
behavior_grounded_family_count
m267_target_preflight_pass_count
joint_direction_target_candidate_count
best_joint_candidate_family
result_class
next_blocker
```

## Route Logic

If one or more primary families pass normal retention, behavior grounding, and
M267/M264 proof retention:

```text
route: direction target export and actor-fit objective design
```

The next actor-fitting design must use the accepted family rows only and must
keep PPO and promotion blocked until exact replay gates are run.

If behavior improves but normal retention fails:

```text
route: amplitude-calibrated direction target audit
```

This means the direction is right, but the target step is outside the current
trust region.

If normal-retained behavior targets pass but M267/M264 proof retention fails:

```text
route: branch-separated direction target refinement
```

This means the low-tail normal branch is actionable, but rejected-history target
handling is unsafe.

If no family remains behavior-grounded after retention:

```text
route: target-source refresh
```

This means the M958 local directions were useful diagnostic moves but are not
valid target candidates.

## Decision For Next Milestone

M959 routes to:

```text
m960-v4-public-base-low-tail-direction-family-target-audit-implementation
```

M960 should implement the no-training direction-family target audit. It must
not train, run PPO, change actor inputs, relax thresholds, use private holdout,
or promote.
