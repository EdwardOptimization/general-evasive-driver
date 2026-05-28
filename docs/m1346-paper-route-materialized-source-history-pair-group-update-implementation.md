# M1346 Paper-Route Materialized Source-History Pair-Group Update Implementation

## Summary

M1346 implements and runs the first bounded no-PPO pair-group objective update
from the M1154 public-gate base.

Result:

```text
materialized_source_history_pair_group_update_group_metric_improved
```

Candidate checkpoint:

```text
runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
```

This is not a checkpoint promotion, not PPO, not private-holdout evidence, and
not a driver-performance or strong self-identification claim. It is an
objective-probe result over the fixed public materialized source-history corpus.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_pair_group_update \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --corpus-run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --row-metrics runs/m1339_materialized_source_history_objective_evaluator/materialized_source_history_objective_rows.csv \
  --run-dir runs/m1346_materialized_source_history_pair_group_update \
  --device cpu
```

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_materialized_source_history_pair_group_update.py
```

Result:

```text
1 passed
```

## Update Scope

Starting checkpoint:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Trainable scope:

```text
response_context_fusion_plus_actor_mean
```

Changed parameters:

```text
actor_mean.bias
actor_mean.weight
response_context_fusion.0.bias
response_context_fusion.0.weight
```

Mutation guard:

```text
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
allowed_parameter_l2: 1.3300853209
allowed_parameter_max_abs: 0.0315537974
```

No actor-input contract change occurred:

```text
checkpoint_contract: canonical_72_human_view_online_recurrent
actor_input_contract_changed: false
labels_enter_actor_input: false
```

## Objective Metrics

Exact row objective before and after:

```text
row_count: 1376
before combined_loss_mean: 6.8847534022
after  combined_loss_mean: 1.9998926339
delta: -4.8848607683
finite_before: true
finite_after: true
```

Exact group objective before and after:

```text
group_count: 688
before group_min_joint_margin_mean: -6.8026667906
after  group_min_joint_margin_mean: -1.1251848645
delta: +5.6774819261
```

Eval fold:

```text
eval_fold: 4
before group_min_joint_margin_mean: -6.4443958161
after  group_min_joint_margin_mean: -1.2625397266
delta: +5.1818560896
eval_fold_no_regression: true
```

Directional group counts:

```text
group_one_sided_conflict_count: 684 -> 605
group_all_rows_both_directional_count: 0 -> 27
group_both_negative_count: 4 -> 26
```

The intended group-min metric improved strongly, including on the held-out eval
fold. The one-sided conflict count also decreased. However, `both_negative`
groups increased from `4` to `26`, so M1346 is a positive objective-probe result
with an important tradeoff that must be audited before replay gates or any
promotion-like decision.

## Fold Summary

Before:

```text
fold 0: group_min_joint_margin_mean -6.8638577117, both_fraction 0.0000
fold 1: group_min_joint_margin_mean -6.9133107909, both_fraction 0.0000
fold 2: group_min_joint_margin_mean -6.6405230042, both_fraction 0.0000
fold 3: group_min_joint_margin_mean -7.1400241045, both_fraction 0.0000
fold 4: group_min_joint_margin_mean -6.4443958161, both_fraction 0.0000
```

After:

```text
fold 0: group_min_joint_margin_mean -1.2093397060, both_fraction 0.0423
fold 1: group_min_joint_margin_mean -1.0384737389, both_fraction 0.0429
fold 2: group_min_joint_margin_mean -1.1474077929, both_fraction 0.0368
fold 3: group_min_joint_margin_mean -0.9690208961, both_fraction 0.0515
fold 4: group_min_joint_margin_mean -1.2625397266, both_fraction 0.0224
```

Every fold improves group-min margin. The weakest all-rows-both-directional
fraction remains small, so the candidate is not a solved source-history
directionality result.

## Interpretation

Supported:

```text
The M1344 pair-group loss is trainable with response_context_fusion + actor_mean
without mutating forbidden parameters.
```

Supported:

```text
The M1336 materialized corpus contains enough gradient signal to improve exact
row and group source-history metrics from the M1154 base.
```

Supported:

```text
The improvement is not train-fold-only overfit by the first check: eval fold 4
also improves in group-min margin.
```

Not supported:

```text
The candidate is a promoted driver checkpoint.
```

Not supported:

```text
The candidate preserves public replay/proof gates.
```

Not supported:

```text
The candidate proves closed-loop self-identification.
```

## Failure And Risk Classification

No evidence of:

```text
contract_violation
private_holdout_contamination
training_instability
forbidden checkpoint mutation
```

Remaining risk:

```text
objective_overfit:
  fixed public source-history objective improved, but closed-loop replay gates
  have not been run.
```

Tradeoff needing audit:

```text
group_both_negative_count increased from 4 to 26 while group-min and one-sided
conflict metrics improved.
```

## Decision

M1346 passes as an infrastructure/objective-probe milestone.

Do not promote the candidate. Do not run PPO from it yet. The next milestone
must audit whether the exact objective improvement is structurally healthy
enough to justify limited replay-gate evaluation.

Next:

```text
m1347-paper-route-materialized-source-history-pair-group-update-result-audit
```
