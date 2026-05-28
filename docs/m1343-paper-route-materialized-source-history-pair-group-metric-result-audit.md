# M1343 Paper-Route Materialized Source-History Pair-Group Metric Result Audit

## Summary

M1343 audits the M1342 group metric result and chooses the next route.

Decision:

```text
materialized_source_history_pair_group_metric_audit_route_to_bounded_update_design
```

The group metrics are clean enough to design a bounded no-PPO objective-update
protocol. They are not positive policy evidence and do not justify an update
yet.

## Evidence

M1342 structural result:

```text
result_class: materialized_source_history_pair_group_metrics_pass
row_count: 1376
group_count: 688
valid_two_condition_group_count: 688
checkpoint_loaded: false
```

M1342 group conflict result:

```text
group_all_rows_both_directional_count: 0
group_all_rows_distance_both_count: 0
group_one_sided_conflict_count: 684
group_both_negative_count: 4
group_one_sided_conflict_fraction: 0.9941860465
group_both_negative_fraction: 0.0058139535
group_min_joint_margin_mean: -6.8026667906
```

This is a clean group-level artifact:

```text
Every group has two condition rows.
No group is fully solved.
Almost every group is one-sided rather than random failure.
```

## Family And Fold Evidence

Every family has group pass fraction `0.0`.

Non-steering families are fully one-sided:

```text
left_right_split_mu: one-sided 1.0
load_cg_perturbation: one-sided 1.0
single_wheel_brake_pull: one-sided 1.0
single_wheel_grip_collapse: one-sided 1.0
tire_blowout_like: one-sided 1.0
```

Steering actuator is almost fully one-sided but contains the 4 both-negative
groups:

```text
steering_actuator_fault:
  one-sided: 0.9791666667
  both-negative: 0.0208333333
```

Every fold has group pass fraction `0.0`. Folds `3` and `4` contain the
both-negative groups.

## Classification

Failure taxonomy:

```text
objective_overfit
```

Specific diagnosis:

```text
pair_group_directional_conflict
```

This is not:

```text
contract_violation;
checkpoint mutation;
private holdout contamination;
single-family overfit;
single-fold artifact;
checkpoint-loading artifact;
random missing-row artifact.
```

## Route Options

Projection repair:

```text
not selected
```

Reason:

```text
The conflict is too structured and exactly mirrored across group rows. The
zero-context source-current projection is still a caveat, but the next useful
variable is an objective design that requires both condition rows to improve.
```

Branch synthesis:

```text
not selected yet
```

Reason:

```text
The branch has one more useful design step before cadence pressure should force
synthesis: a bounded pair-group objective-update design with explicit stop
conditions.
```

Bounded objective-update design:

```text
selected
```

Reason:

```text
The group metric evaluator gives an exact full-corpus residual, expected group
counts, and anti-overfit group keys. It is now possible to design a bounded
no-PPO update protocol without yet running it.
```

## M1344 Requirements

M1344 should design, not run, a bounded no-PPO pair-group objective update.

Required design constraints:

```text
start from current public-gate checkpoint;
freeze log_std;
forbid PPO;
forbid private holdout;
forbid promotion;
forbid actor input changes;
forbid pair-specific weights;
evaluate exact M1339 row metrics and M1342 group metrics before and after;
require group_min_joint_margin improvement;
require group_one_sided_conflict_count reduction;
require no checkpoint mutation outside allowed trainable scope;
route to branch synthesis before implementation if cadence requires it.
```

Candidate trainable scopes should be listed conservatively:

```text
actor_mean_only;
response_context_fusion + actor_mean;
response_encoder + GRU + fusion + actor_mean.
```

Given earlier branch evidence, the design should treat `actor_mean_only` as a
baseline and `response_context_fusion + actor_mean` as the likely first useful
scope, but it must not run either in M1344.

## Unsupported Claims

Still unsupported:

```text
actor update;
PPO continuation;
promotion;
closed-loop driver performance;
paper-level evidence;
strong self-identification.
```

## Decision

Admit one design milestone:

```text
m1344-paper-route-materialized-source-history-pair-group-update-design
```

After M1344, the branch should check cadence before implementation. If the
validator or harness requires synthesis, write synthesis before running any
objective-update probe.
