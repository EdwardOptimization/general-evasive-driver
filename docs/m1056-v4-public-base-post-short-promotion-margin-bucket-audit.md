# M1056 V4 Public Base Post Short-Promotion Margin Bucket Audit

## Purpose

M1056 audits whether M1055's margin-bucket failure is a coarse bucket-edge
artifact or a real margin-diversity sparsity problem.

This milestone does not mine new rows, train, run PPO, use private holdout,
change actor inputs, or promote a checkpoint.

## Input Surface

M1056 reuses the M1055 accepted rows:

```text
runs/m1055_post_short_promotion_boundary_robustness_seed105400/accepted_wrong_history_rows.csv
```

The M1055 surface had:

```text
accepted_wrong_rows: 315
accepted_wrong_physical_pairs: 15
accepted_wrong_left_steps: 7
accepted_wrong_checkpoints: 3
accepted_wrong_targets: 3
accepted_wrong_success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.190476
normal_margin_min: 0.0004777225
normal_margin_mean: 0.0030149320
normal_margin_max: 0.0099828307
```

M1055 failed only because `0.01m` margin buckets produced one bucket.

## Diagnostic Bucket Widths

M1056 reran the same robustness gate with diagnostic bucket widths:

```text
0.0050
0.0025
```

Results:

```text
bucket_width  pass   margin_buckets  accepted_rows  physical_pairs  targets
0.0100        false  1               315            15              3
0.0050        true   2               315            15              3
0.0025        true   4               315            15              3
```

All non-bucket robustness gates remained unchanged and passed:

```text
physical_pairs: 15 >= 10
left_steps: 7 >= 5
checkpoints: 3 >= 3
targets: 3 >= 2
success_drop_fraction: 1.0
max_pair_fraction: 0.190476 <= 0.25
control_accepted_wrong_rows: 0
```

## Margin Bands

The accepted rows are not all at the same margin:

```text
[0.0000, 0.0010): 90
[0.0010, 0.0025): 39
[0.0025, 0.0050): 156
[0.0050, 0.0075): 12
[0.0075, 0.0100): 18
```

This distribution explains the M1055 failure: the pre-registered `0.01m`
bucket width was too coarse for the current near-boundary surface, whose useful
normal margins live inside `0.00-0.01m`.

## Classification

```text
result_class: post_short_promotion_margin_bucket_audit_coarse_bucket_artifact
failure_types: none
```

This is not true surface sparsity:

```text
accepted rows: 315
physical pairs: 15
targets: 3
diagnostic bucket widths: 0.005 and 0.0025 both pass
```

It is a bucket-resolution mismatch after the short-PPO promoted base moved the
active proof surface into a tighter low-margin band.

## Decision

Route to compact corpus conversion design using the M1055 accepted rows and an
explicit `0.005m` current-base margin-bucket rule for this surface family:

```text
m1057-v4-public-base-post-short-promotion-compact-corpus-conversion-design
```

M1057 should not run PPO or train the actor. It should design conversion of the
refreshed rows into compact boundary-outcome objective/replay corpora, with
source caps and replay sanity before any future PPO.

## Decision

```text
post_short_promotion_margin_bucket_audit_route_to_compact_corpus_conversion_design
```

Next:

```text
m1057-v4-public-base-post-short-promotion-compact-corpus-conversion-design
```
