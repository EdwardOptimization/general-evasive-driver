# M1060 V4 Public Base Post Short-Promotion Family-Intersection Corpus Design

## Purpose

M1060 designs a replay-calibrated family-intersection compact corpus after
M1058 showed that current-checkpoint compact rows are not automatically
family-wide proof rows.

This milestone does not filter rows, train, run PPO, use private holdout,
change actor inputs, or promote a checkpoint.

## Problem

M1058 converted the refreshed surface into compact corpora and objective sanity
passed, but one cross-family replay failed:

```text
short61049 corpus -> short61050 candidate:
  baseline_success_drop_count: 27
  candidate_success_drop_count: 24
```

M1059 audited the failed rows as near-zero wrong-history successes under the
repeat checkpoint:

```text
row 0 wrong_history_margin: +0.000086
row 1 wrong_history_margin: +0.000259
row 21 wrong_history_margin: +0.000114
```

The next conversion must only select rows that are proof-valid across the
short-PPO family, not just under the current public-gate base.

## Family

Evaluate:

```text
short61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

Source rows:

```text
runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv
```

## M1061 Tooling

M1061 should add:

```text
src/autodrift/family_intersection_boundary_selector.py
tests/test_family_intersection_boundary_selector.py
```

The selector should preserve original row fields and add:

```text
family_success_drop_count
family_all_normal_success
family_all_wrong_history_fail
family_min_wrong_history_margin
family_min_margin_gap
family_policy_failures
```

## Selection Rule

A row is eligible only if every family policy has:

```text
normal_success == true
wrong_history_success == false
success_drop == true
```

M1061 may report this stricter diagnostic:

```text
family_min_wrong_history_margin <= -0.0001
```

but it should only make that the primary output if the corpus still satisfies:

```text
rows >= 20
physical_pairs >= 10
targets >= 2
```

Compact selection:

```text
max_rows_per_physical_pair: 2
min_rows: 20
min_physical_pairs: 10
min_targets: 2
min_family_success_drop_count: 3
```

Selection priority:

```text
1. rows that pass family intersection;
2. more negative family_min_wrong_history_margin;
3. larger family_min_margin_gap;
4. source diversity across physical_pair_key;
5. target diversity.
```

## Post-Selection Sanity

If the family-intersection selector produces a sufficient compact corpus, M1061
may run the same objective and replay sanity as M1058 on the selected corpus:

```text
objective sanity:
  short61049
  short61050
  short61051

replay sanity:
  selected corpus under all three family policies
```

M1061 still must not run PPO or promote.

## Acceptance

M1061 passes only if:

```text
family-intersection compact rows >= 20
physical pairs >= 10
targets >= 2
all selected rows have success_drop under all family policies
objective sanity passes for all three policies
replay sanity passes for all three policies
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
```

If family-intersection filtering is sparse, route to retargeted mining instead
of relaxing the family-wide proof requirement.

## Decision

```text
post_short_promotion_family_intersection_design_admit_m1061_selector
```

Next:

```text
m1061-v4-public-base-post-short-promotion-family-intersection-corpus
```
