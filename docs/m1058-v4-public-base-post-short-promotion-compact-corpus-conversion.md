# M1058 V4 Public Base Post Short-Promotion Compact Corpus Conversion

## Purpose

M1058 converts the refreshed post-short-promotion surface into compact
objective/replay corpora and runs objective plus cross-family replay sanity.

This milestone does not train the actor, run PPO, use private holdout, change
actor inputs, or promote a checkpoint.

## Input

```text
runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv
```

## Objective Corpus Conversion

All three compact corpora were created:

```text
short61049:
  rows: 27
  physical_pairs: 15
  targets: 3
  objective_pass: true
  seed_pass_count: 3 / 3
  min_val_combined_loss_improvement: 2.173238
  min_val_delta_loss_improvement: 2.758256

short61050:
  rows: 27
  physical_pairs: 15
  targets: 3
  objective_pass: true
  seed_pass_count: 3 / 3
  min_val_combined_loss_improvement: 2.173315
  min_val_delta_loss_improvement: 2.758436

short61051:
  rows: 27
  physical_pairs: 15
  targets: 3
  objective_pass: true
  seed_pass_count: 3 / 3
  min_val_combined_loss_improvement: 2.173764
  min_val_delta_loss_improvement: 2.758950
```

The conversion is not corpus-sparse: every compact corpus satisfies the
pre-registered `>=20` rows, `>=10` physical pairs, and `>=2` targets criteria.

## Cross-Family Replay Sanity

Replay sanity result:

```text
short61049 corpus, candidate short61050:
  baseline_success_drop_count: 27
  candidate_success_drop_count: 24
  gate_pass: false

short61050 corpus, candidate short61049:
  baseline_success_drop_count: 27
  candidate_success_drop_count: 27
  gate_pass: true

short61051 corpus, candidate short61049:
  baseline_success_drop_count: 27
  candidate_success_drop_count: 27
  gate_pass: true
```

The failing gate preserved normal success and margin retention:

```text
normal_success_delta: 0.0
normal_margin_mean_delta: +0.000315
margin_gap_mean_delta: -0.000011
```

but failed success-drop retention:

```text
success_drop_count_delta: -3
```

## Failed Rows

The three failed rows in the `short61049 -> short61050` replay are:

```text
row 0:
  target: future_braking_deceleration
  physical_pair_key: 105426:15:105438:42
  wrong_history_success: true
  wrong_history_margin: +0.000086

row 1:
  target: future_braking_deceleration
  physical_pair_key: 105426:15:105438:39
  wrong_history_success: true
  wrong_history_margin: +0.000259

row 21:
  target: future_lateral_accel_response
  physical_pair_key: 105422:3:105441:3
  wrong_history_success: true
  wrong_history_margin: +0.000114
```

The wrong-history successes are near-boundary positive, not large-margin safe
rollouts. This suggests the compact conversion selected rows that are valid
for the current checkpoint but not all repeat-family checkpoints under strict
cross-family replay.

## Classification

```text
result_class: post_short_promotion_compact_corpus_conversion_replay_failure
failure_types: proof_washout
```

This is not:

```text
objective_sanity_failure
compact_corpus_sparse
actor_contract_violation
training_instability
```

It is a cross-family replay retention failure after successful objective
conversion.

## Decision

Do not use the M1058 compact corpus as a gate yet and do not route to PPO.

Next step:

```text
m1059-v4-public-base-post-short-promotion-conversion-replay-failure-audit
```

M1059 should audit whether the failure is due to:

```text
1. row-level wrong-history positive-margin edge cases;
2. current-base-only versus family-wide corpus mismatch;
3. compact corpus selection caps selecting unstable rows;
4. missing replay-calibrated row filters such as wrong_history_margin < -epsilon.
```

## Decision

```text
post_short_promotion_compact_corpus_conversion_replay_failure_route_to_audit
```

Next:

```text
m1059-v4-public-base-post-short-promotion-conversion-replay-failure-audit
```
