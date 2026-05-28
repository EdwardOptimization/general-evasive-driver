# M1341 Paper-Route Materialized Source-History Pair-Group Objective Design

## Summary

M1341 designs the group-level objective needed after M1340 classified the
M1339 evaluator result as a two-condition directional conflict.

Decision:

```text
materialized_source_history_pair_group_objective_design_admit_group_metric_evaluator
```

Do not train.

Do not run PPO.

Do not update actor weights.

The next milestone should implement a no-update group metric evaluator:

```text
m1342-paper-route-materialized-source-history-pair-group-metric-evaluator
```

## Problem

M1339 produced finite exact row metrics, but M1340 showed the target conflict:

```text
684 rows: correct-negative / wrong-positive
684 rows: correct-positive / wrong-negative
8 rows:   both-negative
0 rows:   both-positive
```

Grouping by `source_identity + probe_template` gives:

```text
684 groups: one condition row on each one-sided quadrant
4 groups:   both rows both-negative
0 groups:   both rows both-positive
```

Therefore a rowwise scalar update is unsafe. It can reduce loss by improving one
condition while preserving or worsening the paired condition conflict.

## Group Unit

Use this group key:

```text
group_id = source_identity + "|" + probe_template
```

Expected group structure:

```text
group_count: 688
rows_per_group: 2
conditions_per_group: A and B
source_identity preserved
probe_template preserved
source_family inherited from rows
fold inherited from rows
```

Any group with missing condition rows, duplicate condition rows, mixed
source_identity, or mixed probe template is a contract failure for the group
metric evaluator.

## Row Margins

For each row:

```text
m_correct = correct_preference_margin
m_wrong   = wrong_history_preference_margin
m_dist_c  = correct_distance_to_rejected - correct_distance_to_preferred
m_dist_w  = wrong_distance_to_preferred - wrong_distance_to_rejected
```

Row pass definitions:

```text
row_logprob_both = m_correct > 0 and m_wrong > 0
row_distance_both = m_dist_c > 0 and m_dist_w > 0
row_joint_margin = min(m_correct, m_wrong)
row_distance_joint_margin = min(m_dist_c, m_dist_w)
```

## Group Metrics

For each group:

```text
group_min_joint_margin = min(row_joint_margin over rows)
group_mean_joint_margin = mean(row_joint_margin over rows)
group_min_correct_margin = min(m_correct over rows)
group_min_wrong_margin = min(m_wrong over rows)
group_all_rows_both_directional = all(row_logprob_both)
group_all_rows_distance_both = all(row_distance_both)
group_one_sided_conflict =
  one row is correct-positive/wrong-negative
  and the paired row is correct-negative/wrong-positive
group_both_negative = all rows are correct-negative/wrong-negative
```

The group evaluator should also write per-family and per-fold summaries:

```text
group_all_rows_both_directional_fraction
group_one_sided_conflict_fraction
group_both_negative_fraction
group_min_joint_margin_mean
worst_family_group_pass_fraction
worst_fold_group_pass_fraction
```

## Objective Shape For Later Updates

M1341 does not implement an actor update, but it defines the objective that a
later design may use after the group metric evaluator is audited.

Row preference loss remains:

```text
L_row = L_correct + L_wrong
```

Add a group-min term:

```text
L_group_min =
  mean_over_groups softplus(m_group - group_min_joint_margin)
```

Default:

```text
m_group = 0.05
```

Add a condition balance term:

```text
L_condition_balance =
  mean_over_groups abs(row_joint_margin_A - row_joint_margin_B)
```

Purpose:

```text
discourage solving A by worsening B, or solving B by worsening A
```

Potential later combined objective:

```text
L_pair_group =
  L_row
  + lambda_group_min * L_group_min
  + lambda_balance * L_condition_balance
```

Initial design defaults for later evaluation only:

```text
lambda_group_min = 1.0
lambda_balance = 0.1
```

These are design defaults, not approved training hyperparameters.

## Anti-Overfit Guards

M1341 explicitly forbids:

```text
pair-specific weights;
source_identity-specific tuning;
dropping hard groups;
optimizing only the 4 both-negative groups;
optimizing one condition without paired-condition reporting;
promoting from group metrics alone;
private holdout use;
PPO escalation.
```

Allowed grouping summaries:

```text
source_family
fold
probe_template
condition
margin bucket
```

These summaries are diagnostic only. They may inform a future design, but a
future update must not hide one-sided conflict by changing per-pair weights.

## M1342 No-Update Evaluator

M1342 should implement:

```text
src/autodrift/materialized_source_history_pair_group_metrics.py
tests/test_materialized_source_history_pair_group_metrics.py
```

Input:

```text
runs/m1339_materialized_source_history_objective_evaluator/materialized_source_history_objective_rows.csv
```

Output:

```text
runs/m1342_materialized_source_history_pair_group_metrics/summary.json
runs/m1342_materialized_source_history_pair_group_metrics/group_rows.csv
runs/m1342_materialized_source_history_pair_group_metrics/family_group_summary.csv
runs/m1342_materialized_source_history_pair_group_metrics/fold_group_summary.csv
```

Expected structural metrics:

```text
row_count: 1376
group_count: 688
valid_two_condition_group_count: 688
group_all_rows_both_directional_count: 0
group_one_sided_conflict_count: 684
group_both_negative_count: 4
```

M1342 should not load a policy checkpoint or rerun the actor. It should only
convert M1339 exact row metrics into group metrics and objective-readiness
diagnostics.

## Decision

Admit one no-update group metric evaluator:

```text
m1342-paper-route-materialized-source-history-pair-group-metric-evaluator
```

Only after M1342 is audited should the project consider a bounded objective-only
update design.
