# M1311 Paper-Route Source-History Robust Min-Fold Objective Design

## Summary

M1311 designs the next no-PPO source-history objective after M1310 showed that
simple group weighting is not robust.

Decision:

```text
source_history_robust_minfold_objective_design_admit_bounded_probe
```

The next implementation should not increase scalar group weights and should not
route to PPO. It should make fold-level non-regression a first-class objective:
protect folds that already pass, then improve failed folds, while preserving
group-level no pair-specific-weight discipline.

## Input Evidence

M1310 classified M1309 as:

```text
weighted_repeat_top_combo_partial_improvement_global_regression
```

Key M1310 facts:

```text
baseline_repeat_offset_pass_count: 3
weighted_repeat_offset_pass_count: 1
lost_pass_offsets: 0|1
eval_improved_offsets: 3|4
eval_regressed_offsets: 0|1|2
best_weighted_offset: 3
best_weighted_eval_delta: 0.1517857143
top_failed_combo_positive_delta: +3
full_improved_to_positive_count: 30
full_regressed_from_positive_count: 32
full_mean_margin_delta: -0.0151337285
```

Interpretation:

```text
M1309 found a real local direction, but it bought that direction by losing
baseline passing folds. The next objective must optimize a robust fold-level
criterion, not a weighted mean.
```

## Design Constraints

Hard constraints:

- No PPO.
- No promotion.
- No private holdout.
- No actor input changes.
- No pair-specific weights.
- No threshold relaxation.
- No closed-loop self-identification or paper-level claim.

Method constraints:

- The repeat probe remains pair-disjoint.
- Each split candidate trains only on its train split.
- Held-out eval rows are used only for evaluation and pass/fail decisions.
- Public diagnostic rows remain public proof/development rows, not private
  evidence.

## Objective Structure

For each split offset `k`, define:

```text
T_k = train rows for split k
E_k = held-out eval rows for split k
G_k = pair_id/probe_template groups inside T_k
B_k = source-family/probe/margin-bucket groups inside T_k
```

Use the existing correct-history and wrong-history directional margins:

```text
m_i = min(correct_margin_i, wrong_history_margin_i)
```

The base directional term remains:

```text
L_directional =
  mean_i softplus(target_margin - correct_margin_i)
+ mean_i softplus(target_margin - wrong_history_margin_i)
```

The group floor term remains group-level rather than pair-specific:

```text
L_group_floor =
  mean_g softplus(target_margin - min_{i in g} m_i)
```

Add a robust bucket/CVaR term:

```text
L_bucket_cvar =
  mean_b softmax_tau({softplus(target_margin - min_{i in g} m_i): g in b})
```

where `b` is a public diagnostic bucket such as:

```text
source_family_pair x probe_template
source_family_pair x probe_template x margin_bucket
```

This attacks concentrated failures without assigning custom weights to a pair.

Add a passing-fold retention term for train groups that were already positive
under the M1302 baseline candidate for the same split offset:

```text
L_retention =
  mean_{g in retained_train_groups}
    softplus((baseline_group_margin_g - retention_eps) - current_group_margin_g)
```

This term protects already working surfaces. It is train-split only for the
implementation probe, so held-out eval rows are not trained on.

The total no-PPO objective:

```text
L =
  L_directional
+ lambda_floor * L_group_floor
+ lambda_bucket * L_bucket_cvar
+ lambda_retention * L_retention
+ lambda_anchor * parameter_anchor
```

The important change is not another scalar group-weight boost. It is the
lexicographic rule used to accept or reject a candidate.

## Lexicographic Acceptance

A candidate is not accepted because its average loss improves. It must pass the
following order:

1. No forbidden parameter mutation.
2. No actor input contract change.
3. No pair-specific weights.
4. No lost pass on M1302 baseline passing offsets `0|1|3`.
5. Repeat pass count is at least M1302: `>= 3/5`.
6. Mean eval row/group fractions are at least M1302:

```text
mean_eval_both_directional_fraction >= 0.2335317460
mean_eval_group_all_rows_both_positive_fraction >= 0.2335317460
```

7. Mean full counts are at least M1302:

```text
mean_full_both_positive_count >= 38.0
mean_full_group_all_rows_both_positive_count >= 19.0
```

8. Top failed combo is not worse:

```text
top_failed_combo_positive_delta >= 0
top_failed_combo_mean_margin_delta >= -0.005
```

Only after these retention criteria pass can the candidate be described as a
repeat improvement candidate.

## M1312 Implementation Plan

M1312 should extend the existing trainable-scope repeat probe rather than
creating a second training path.

Proposed CLI additions:

```text
--baseline-repeat-run-dir runs/m1302_source_history_trainable_scope_repeat_probe
--robust-minfold
--bucket-columns source_family_pair,probe_template,margin_bucket
--lambda-bucket-cvar 2.0
--lambda-retention 2.0
--retention-margin-eps 0.02
--minfold-temperature 0.25
```

Required output artifacts:

```text
runs/m1312_source_history_robust_minfold_probe/summary.json
runs/m1312_source_history_robust_minfold_probe/scope_summaries.csv
runs/m1312_source_history_robust_minfold_probe/offset_comparison.csv
runs/m1312_source_history_robust_minfold_probe/retention_group_diagnostics.csv
runs/m1312_source_history_robust_minfold_probe/bucket_cvar_diagnostics.csv
```

M1312 should also run the M1310 tradeoff audit on its result, so the outcome is
directly comparable to M1302 and M1309.

## Pass Criteria For M1312

M1312 passes as no-PPO diagnostic infrastructure if:

```text
forbidden_parameter_mutation_detected: false
pair_specific_weight_used: false
baseline_pass_lost_offsets: ""
repeat_offset_pass_count >= 3
mean_eval_both_directional_fraction >= 0.2335317460
mean_full_both_positive_count >= 38.0
top_failed_combo_positive_delta >= 0
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

It does not need to promote a checkpoint. It only needs to show that robust
fold-aware objective design is better than M1309's weighted mean.

## Failure Routing

If M1312 again produces one strong split but loses baseline passing offsets:

```text
route to source-history corpus expansion or branch synthesis
```

If M1312 protects passing offsets but cannot improve failed offsets:

```text
route to corpus expansion or sequence/trajectory-level source-history targets
```

If M1312 passes repeat robustness:

```text
route to result audit before any public replay gate or PPO
```

## Claims

Allowed claim:

```text
M1311 defines a no-PPO robust fold-aware objective protocol for fixed-current
source-history diagnostics.
```

Not allowed:

```text
driver performance improved
closed-loop self-identification is proven
PPO is admitted
checkpoint promotion is admitted
paper-level evidence is established
```
