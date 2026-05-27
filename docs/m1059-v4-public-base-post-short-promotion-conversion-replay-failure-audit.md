# M1059 V4 Public Base Post Short-Promotion Conversion Replay Failure Audit

## Purpose

M1059 audits the M1058 failure where compact objective conversion passed but
one cross-family replay sanity gate lost three success-drop rows.

This milestone does not train, run PPO, use private holdout, change actor
inputs, promote a checkpoint, or alter the corpus.

## Failure Summary

M1058 objective conversion passed:

```text
objective_pass_count: 3 / 3
compact rows per corpus: 27
physical pairs per corpus: 15
targets per corpus: 3
```

M1058 replay sanity:

```text
short61049 corpus -> short61050 candidate:
  baseline_success_drop_count: 27
  candidate_success_drop_count: 24
  gate_pass: false

short61050 corpus -> short61049 candidate:
  baseline_success_drop_count: 27
  candidate_success_drop_count: 27
  gate_pass: true

short61051 corpus -> short61049 candidate:
  baseline_success_drop_count: 27
  candidate_success_drop_count: 27
  gate_pass: true
```

The failed replay preserved normal-history success:

```text
normal_success_delta: 0.0
normal_margin_mean_delta: +0.000315
margin_gap_mean_delta: -0.000011
```

The failure is specifically wrong-history success-drop retention.

## Failed Rows

The three failed rows are:

```text
row 0:
  target: future_braking_deceleration
  physical_pair_key: 105426:15:105438:42
  wrong_history_success under short61050: true
  wrong_history_margin: +0.000086

row 1:
  target: future_braking_deceleration
  physical_pair_key: 105426:15:105438:39
  wrong_history_success under short61050: true
  wrong_history_margin: +0.000259

row 21:
  target: future_lateral_accel_response
  physical_pair_key: 105422:3:105441:3
  wrong_history_success under short61050: true
  wrong_history_margin: +0.000114
```

These are near-zero positive margins. They are not broad safe wrong-history
rollouts. The failure is therefore a replay-calibration issue at the compact
row selection boundary.

## Classification

```text
result_class: post_short_promotion_conversion_replay_failure_audit
failure_types: proof_washout
failure_subtype: family_intersection_replay_filter_missing
```

The compact corpus is not too small and the objective is learnable. The missing
piece is that rows selected from the current checkpoint are not guaranteed to
remain wrong-history failures across the short-PPO family.

## Decision

Do not use the M1058 compact corpus as a gate yet.

Route to a family-intersection replay-calibrated conversion design:

```text
m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design
```

M1060 should design a selector that starts from M1055/M1056 accepted rows and
keeps only rows that replay as:

```text
normal_success == true
wrong_history_success == false
```

under all short-PPO family checkpoints:

```text
short61049
short61050
short61051
```

It should also consider a conservative wrong-history margin filter:

```text
wrong_history_margin <= -0.0001
```

but only if the resulting corpus still satisfies:

```text
rows >= 20
physical_pairs >= 10
targets >= 2
max_rows_per_physical_pair <= 2
```

## Decision

```text
post_short_promotion_conversion_replay_failure_route_to_family_intersection_design
```

Next:

```text
m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design
```
