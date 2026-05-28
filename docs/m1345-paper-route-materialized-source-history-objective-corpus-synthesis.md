# M1345 Paper-Route Materialized Source-History Objective Corpus Synthesis

## Summary

M1345 synthesizes the `paper_route_materialized_source_history_objective_corpus`
branch from M1335 through M1344.

Synthesis decision:

```text
promote_to_next_branch
```

New branch:

```text
paper_route_materialized_source_history_pair_group_update_implementation
```

Next milestone:

```text
m1346-paper-route-materialized-source-history-pair-group-update-implementation
```

This is not a checkpoint promotion and not driver evidence. It is a workflow
decision to close the corpus/evaluator branch and open a bounded no-PPO update
implementation branch.

## Evidence Summary

M1335 designed an active materialized source-history objective corpus from the
M1333 materialized histories.

M1336 implemented the export:

```text
active_source_pair_rows: 344
active_history_prefix_rows: 1376
active_history_frame_rows: 33024
active_history_intervention_rows: 1376
active_wrong_history_pair_rows: 1376
active_source_family_count: 6
active_zero_response_l2_prefix_count: 0
```

M1336 also preserved quarantines:

```text
halfshaft_probe_silent: 22 source pairs, 88 prefixes
global_friction_missing: explicit missing-family row
```

M1337 audited the export as admissible and blocked objective work until the
active/quarantine semantics were explicit.

M1338 designed a no-update exact evaluator for the active corpus.

M1339 implemented the evaluator:

```text
row_count: 1376
finite_row_count: 1376
projection_valid_count: 1376
wrong_history_valid_count: 1376
checkpoint_weights_mutated: false
combined_loss_mean: 6.8847534022
history_action_l2_mean: 0.0635018957
both_directional_fraction: 0.0
```

M1340 audited this as a two-condition directional conflict:

```text
684 rows: correct-negative / wrong-positive
684 rows: correct-positive / wrong-negative
8 rows: both-negative
0 rows: both-positive
```

M1341 designed group-level objective semantics using:

```text
group_id = source_identity|probe_template
```

M1342 implemented group metrics:

```text
group_count: 688
valid_two_condition_group_count: 688
group_all_rows_both_directional_count: 0
group_one_sided_conflict_count: 684
group_both_negative_count: 4
group_min_joint_margin_mean: -6.8026667906
```

M1343 selected bounded pair-group objective-update design as the next route.

M1344 designed that update protocol and then correctly routed to branch
synthesis before implementation.

## Supported Claims

Supported:

```text
The branch produced a clean active materialized source-history corpus with
explicit quarantines.
```

Supported:

```text
The no-update evaluator can compute finite full-corpus source-history residuals
without checkpoint mutation.
```

Supported:

```text
The current public-gate checkpoint reacts to materialized histories, because
history_action_l2_mean is nonzero.
```

Supported:

```text
The current checkpoint does not solve the pair-group directionality target; the
failure is group-structured and broad across source families and folds.
```

Supported:

```text
A bounded no-PPO pair-group objective-update branch is now well specified enough
to implement one controlled probe.
```

## Falsified Claims

Falsified:

```text
The current public-gate checkpoint already maps correct histories to preferred
actions and wrong histories to rejected actions on the M1336 corpus.
```

Falsified:

```text
A rowwise scalar source-history objective is sufficient without grouping paired
condition rows.
```

Falsified:

```text
Current brake/lift probes create usable halfshaft response-history evidence.
```

Still unsupported:

```text
global friction coverage;
closed-loop driver performance;
paper-level evidence;
strong self-identification.
```

## Failure Taxonomy Summary

Retained source-coverage blockers:

```text
scenario_sampling_failure:
  halfshaft_probe_silent
  global_friction_missing
```

Objective/evidence blocker:

```text
objective_overfit:
  materialized_source_history_two_condition_directional_conflict
  pair_group_directional_conflict
```

No evidence of:

```text
contract_violation;
checkpoint mutation;
private holdout contamination;
training instability;
promotion gate failure.
```

## Public-Gate Overfit Risk

Risk:

```text
high
```

Reasons:

```text
The corpus is public and has shaped several branch decisions.
The evaluator uses zero-context source-current observations.
The objective is fixed-current diagnostic evidence, not closed-loop proof.
The next update would optimize directly against this public source-history
surface.
```

Risk controls for the next branch:

```text
no checkpoint promotion from M1346;
no private holdout use;
no PPO;
exact before/after M1339 and M1342 metrics;
fold-level train/eval reporting;
forbidden parameter mutation checks;
result audit before any replay or larger update.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

New branch:

```text
paper_route_materialized_source_history_pair_group_update_implementation
```

First milestone:

```text
m1346-paper-route-materialized-source-history-pair-group-update-implementation
```

M1346 may implement one bounded no-PPO update probe. It must:

```text
start from M1154 public-gate base;
use response_context_fusion + actor_mean as the first trainable scope;
freeze log_std and all non-selected parameters;
train only on declared public/source folds;
evaluate exact M1339 and M1342 metrics before and after;
write parameter mutation diagnostics;
avoid PPO, private holdout, promotion, and actor-input changes.
```

M1346 must not claim driver performance or self-identification. It can only test
whether the pair-group objective can reduce the exact fixed source-history
conflict without breaking basic invariants.

## Decision

Close:

```text
paper_route_materialized_source_history_objective_corpus
```

Open:

```text
paper_route_materialized_source_history_pair_group_update_implementation
```
