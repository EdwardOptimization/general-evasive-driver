# M957 V4 Public Base Low-Tail Target Metric Artifact Audit Design

## Purpose

M957 designs the next no-training audit after M956.

It does not train, run PPO, update model weights, change actor inputs, relax
thresholds, use private holdout, or promote.

M956 showed that delayed low-tail projection sequences preserve both
first-action retention and M267 proof retention, but terminal margin worsens on
the evaluated low-tail rows. That makes the current low-tail action-gap target
suspect.

The next question is:

```text
Is the low-tail action-gap metric behaviorally grounded, or is it a target
metric artifact for this branch?
```

## Evidence From M956

M956 result:

```text
sequence_family_count: 9
first_action_retained_family_count: 9
m267_sequence_preflight_pass_count: 9
sequence_low_tail_candidate_count: 0
terminal_margin_positive_family_count: 0
joint_sequence_candidate_count: 0
```

Best sequence family:

```text
family: delayed_projection_h2_amp_0_0040
terminal_margin_mean_delta: -0.000018
positive_margin_fraction: 0.0
prefix_l2_mean: 0.001000
```

The failure is not M267 proof washout and not first-action retention. It is
that the action-gap based low-tail direction does not improve closed-loop
terminal margin.

## Audit Question

M958 should answer:

```text
When a candidate improves the low-tail action-gap proxy, does terminal margin
also improve?
```

If not, the branch should stop optimizing that proxy as a target and redefine
the low-tail target around closed-loop margin or recoverability.

## Candidate Direction Families

M958 should evaluate multiple no-training direction families on the same
low-tail rows used by M956. This is important: a bad sign or bad action axis can
look like a metric artifact unless direction alternatives are tested.

### A. Away From Intervention

This is the M954/M956 direction:

```text
delta = normal_action - intervention_action
```

It should reproduce M956's negative terminal-margin trend.

### B. Toward Intervention

Reverse the sign:

```text
delta = intervention_action - normal_action
```

If this improves terminal margin while worsening action-gap metrics, then the
previous target direction is likely sign-wrong for the closed-loop behavior.

### C. Action-Axis Families

Evaluate simple actuator axes:

```text
steer_plus
steer_minus
brake_plus
brake_minus
throttle_plus
throttle_minus
steer_plus_brake_plus
steer_minus_brake_plus
```

These are not rules for the final driver. They are no-training diagnostic
directions to identify whether the proxy is pushing the wrong actuator axis.

### D. Existing M951 Direction Families

Include the M951 existing direction at alpha-like scales:

```text
0.0500 direction: normal retained, no tail lift
0.0675 direction: tail lift, retention miss
```

Compare their action-gap proxy changes against terminal margin changes.

## Metrics

M958 must report both proxy metrics and closed-loop behavior metrics for each
candidate family.

### Proxy Metrics

For each row/family:

```text
first_action_l2
prefix_l2_mean
normal_intervention_gap_delta
gap_deficit_delta
low_tail_proxy_improved
```

`low_tail_proxy_improved` is true only if the candidate improves the registered
action-gap objective relative to the base row.

### Behavior Metrics

For each row/family:

```text
terminal_margin_delta
success_delta
collision_delta
terminal_reason_changed
positive_margin
```

`behavior_improved` is true if terminal margin improves without new collision
or success regression.

### Grounding Metrics

Aggregate per family:

```text
proxy_improved_fraction
behavior_improved_fraction
proxy_and_behavior_improved_fraction
proxy_improved_behavior_worse_fraction
spearman_proxy_vs_margin
sign_agreement_rate
```

The branch should classify the low-tail proxy as ungrounded if:

```text
proxy_improved_fraction >= 0.50
and proxy_and_behavior_improved_fraction < 0.20
and proxy_improved_behavior_worse_fraction >= 0.50
```

It should classify direction-sign suspicion if:

```text
away_from_intervention: proxy improves but margin worsens
toward_intervention: proxy worsens but margin improves
```

It should classify threshold-only issue only if proxy and behavior generally
agree, but strict thresholds reject candidates.

## Required Artifacts For M958

M958 should write:

```text
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/summary.json
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/direction_family_summary.csv
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/row_metric_grounding.csv
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/proxy_behavior_correlation.csv
runs/m958_v4_public_base_low_tail_target_metric_artifact_audit/route_decision.csv
```

The summary must include:

```text
training_started: false
ppo_used: false
promoted: false
actor_input_contract_changed: false
direction_family_count
evaluated_low_tail_rows
proxy_improved_behavior_worse_family_count
behavior_improved_family_count
direction_sign_suspicion
target_metric_artifact
threshold_only_issue
result_class
next_blocker
```

## Route Logic

If `target_metric_artifact=true`:

```text
route: low-tail target redefinition design
```

The next target should be grounded in closed-loop terminal margin,
recoverability, or outcome-sensitive local action search rather than raw
normal/intervention action-gap.

If `direction_sign_suspicion=true`:

```text
route: direction-family target audit
```

This means the proxy may be useful, but the current direction is wrong.

If `threshold_only_issue=true`:

```text
route: exact threshold sensitivity audit
```

This route is only allowed if proxy improvement and terminal margin improvement
are positively correlated.

If no direction family changes terminal margin materially:

```text
route: target-source refresh
```

This means the sampled low-tail rows may not be actionable by local target
changes and should be refreshed from more outcome-sensitive sources.

## Decision For Next Milestone

M957 routes to:

```text
m958-v4-public-base-low-tail-target-metric-artifact-audit-implementation
```

M958 should implement the no-training metric-grounding audit. It must not
train, run PPO, change actor inputs, relax thresholds, or promote.
