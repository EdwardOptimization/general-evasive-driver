# M1340 Paper-Route Materialized Source-History Objective Evaluator Result Audit

## Summary

M1340 audits the M1339 exact no-update evaluator result before any objective
update.

Decision:

```text
materialized_source_history_objective_evaluator_audit_directional_conflict_route_to_pair_group_design
```

M1339 is a valid evaluator result, but it is not a positive policy-side
source-history gate. The result shows a structured two-condition directional
conflict.

## Structural Gate

M1339 passes infrastructure:

```text
result_class: materialized_source_history_objective_evaluator_pass
row_count: 1376
finite_row_count: 1376
projection_valid_count: 1376
wrong_history_valid_count: 1376
active_quarantine_rows_used: 0
exact_objective_finite: true
checkpoint_weights_mutated: false
```

This means the evaluator is usable. It does not mean the current checkpoint has
solved the source-history objective.

## Directional Result

Exact objective:

```text
combined_loss_mean: 6.8847534022
correct_preference_loss_mean: 3.4480423585
wrong_history_preference_loss_mean: 3.4367110436
```

Aggregate fractions:

```text
correct_preference_positive_fraction: 0.4970930233
wrong_history_preference_positive_fraction: 0.4970930233
both_directional_fraction: 0.0
correct_closer_to_preferred_fraction: 0.4970930233
wrong_closer_to_rejected_fraction: 0.4970930233
both_distance_directional_fraction: 0.0
```

History action movement:

```text
history_action_l2_mean: 0.0635018957
history_action_l2_p10: 0.0023122903
history_action_l2_p50: 0.0072870062
history_action_l2_p90: 0.2372618015
```

Interpretation:

```text
The checkpoint responds to histories, but the response is not aligned with the
two-sided preferred/rejected source-history target.
```

## Quadrant Audit

Log-probability sign quadrants:

```text
correct negative, wrong positive: 684
correct positive, wrong negative: 684
correct negative, wrong negative: 8
correct positive, wrong positive: 0
```

Action-distance sign quadrants:

```text
correct farther, wrong closer: 684
correct closer, wrong farther: 684
correct farther, wrong farther: 8
correct closer, wrong closer: 0
```

The zero both-directional result is not caused by one metric only. Log-prob and
action-distance diagnostics agree.

## Condition Audit

By condition:

```text
condition A:
  c-/w+: 478
  c+/w-: 206
  c-/w-: 4

condition B:
  c+/w-: 478
  c-/w+: 206
  c-/w-: 4
```

The conflict flips with condition. This is the main signal: the current
checkpoint tends to fit one side of the two-condition pair and miss the other.

## Probe And Family Audit

By probe:

```text
left_brake_probe:
  c-/w+: 342
  c+/w-: 342
  c-/w-: 4

right_brake_probe:
  c-/w+: 342
  c+/w-: 342
  c-/w-: 4
```

By family:

```text
left_right_split_mu: 74 c-/w+, 74 c+/w-
load_cg_perturbation: 108 c+/w-, 108 c-/w+
single_wheel_brake_pull: 124 c-/w+, 124 c+/w-
single_wheel_grip_collapse: 128 c-/w+, 128 c+/w-
steering_actuator_fault: 188 c-/w+, 188 c+/w-, 8 c-/w-
tire_blowout_like: 62 c-/w+, 62 c+/w-
```

This is not a single-family or single-probe artifact. It is a balanced
two-condition group conflict.

## Group Audit

Grouping by:

```text
source_identity + probe_template
```

Group status:

```text
684 groups:
  two rows per group
  one row correct-positive/wrong-negative
  one row correct-negative/wrong-positive

4 groups:
  two rows per group
  both rows correct-negative/wrong-negative
```

There are no groups where both condition rows are both-directional positive.

## Classification

Failure taxonomy:

```text
objective_overfit
```

More precise diagnosis:

```text
materialized_source_history_two_condition_directional_conflict
```

This is not a training failure because no training occurred. It is not a
checkpoint-mutation issue, contract violation, private-holdout issue, or
source-family singleton. It is a target/objective-geometry issue: a rowwise
source-history residual is finite but conflicts across the two condition rows
inside each source/probe group.

## Route Decision

Do not run a rowwise scalar objective update from M1339.

Do not run PPO.

Do not promote.

Route to one design milestone:

```text
m1341-paper-route-materialized-source-history-pair-group-objective-design
```

M1341 should design a group-level objective that treats each
`source_identity/probe_template` two-condition group as the unit of work. The
objective should protect against solving one condition by worsening the other,
using group-min or lexicographic terms before any actor update.

## Remaining Caveats

The M1339 evaluator uses a same-current source observation with zero scene
context. Therefore M1340 still does not support:

```text
closed-loop driver performance;
paper-level evidence;
strong self-identification;
halfshaft self-identification;
global friction coverage.
```

The next branch step should stay no-training until the pair-group objective is
specified.
