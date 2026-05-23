# M372 Old-Key Gap-Distribution Retention Design

M372 designs how old-key compact gap-tail failures feed back into the
differentiable repair path. It does not run PPO, promote alpha `0.6`, lower
old-key thresholds, or change actor inputs.

## Problem

M370 promoted:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
```

M371 found the first tested failure along the same repair direction:

```text
runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_6.pt
```

Alpha `0.6` keeps all compact old-key rows accepted:

```text
accepted rows: 40 / 40
normal-success rows: 40 / 40
candidate accepted regressions: 0
candidate normal-success regressions: 0
```

It fails only the lower-tail gap-distribution gate:

```text
candidate gap p10 = -0.000573217
threshold = -0.0005
```

This differs from M366. M366 was a single accepted-regression sign crossing.
M371 is a lower-tail gap erosion with no accepted regression.

## Design Principle

Closed-loop old-key replay remains authoritative. The differentiable repair
corpus is a guide for candidate generation, not the proof gate.

The repair feedback should separate two failure classes:

| Failure class | Example | Feedback |
| --- | --- | --- |
| accepted-regression hard row | M366 alpha `0.2` row 9951 | strong wrong-branch / rejected-action pressure |
| gap-tail erosion row | M371 alpha `0.6` lower-tail rows | balanced normal/wrong retention pressure to preserve margin-gap distribution |

Do not lower the old-key gap-p10 floor. If a future candidate passes only after
relaxing `-0.0005`, it is not a proof-gate pass.

## Gap-Tail Overlay Schema

Extend the optional old-key overlay with gap-tail columns:

```text
case_id
gap_tail_row
gap_tail_reason
gap_weight_multiplier
normal_branch_weight_multiplier
wrong_branch_weight_multiplier
reference_policy
candidate_policy
reference_margin_gap
candidate_margin_gap
candidate_gap_delta
candidate_normal_delta
candidate_wrong_delta
target_gap_delta_floor
target_gap_delta_buffer
candidate_gap_p10_regression
```

The M371 tail rows should be exported from:

```text
runs/m371_alpha06_gap_audit/alpha04_alpha06_gap_audit_rows.csv
```

Initial selection rule:

```text
gap_tail_row = candidate_gap_delta < -0.0005
```

Keep all rows with `candidate_gap_delta < -0.0005` from alpha `0.6`, not only
the marginal row. For M371 that is five rows:

```text
10033|perturbed|29|23|9.500000|-1.200000|0.700000
9982|perturbed|45|39|9.500000|-1.200000|0.700000
10033|perturbed|26|23|9.500000|-1.200000|0.700000
10033|perturbed|26|23|9.500000|-1.200000|0.800000
9907|perturbed|27|18|10.500000|-1.200000|0.700000
```

## Weighting Policy

Use branch weights based on which side eroded the gap:

```text
gap_delta = normal_delta - wrong_delta
```

If `normal_delta` is negative, increase preferred/normal branch retention.

If `wrong_delta` is positive, increase wrong-history/rejected branch retention,
because a safer wrong-history branch shrinks the proof gap.

Recommended initial multipliers:

```text
gap_weight_multiplier = 4.0
normal_branch_weight_multiplier =
  1.0 + 8.0 * clip(-candidate_normal_delta / 0.001, 0, 2)
wrong_branch_weight_multiplier =
  1.0 + 8.0 * clip(candidate_wrong_delta / 0.001, 0, 2)
```

These are training-time metadata. They must not enter actor observation.

## Corpus Changes

Extend `old_key_preference_corpus.py` to merge both accepted-regression
hard-row metadata and gap-tail metadata.

Optional NPZ arrays should include:

```text
hard_row
gap_tail_row
preferred_branch_weight
wrong_branch_weight
```

For backward compatibility:

- no overlay means the NPZ stays in the old format;
- hard-row-only overlay behaves as M368;
- gap-tail overlay adds `gap_tail_row` and branch weights;
- branch-weighted repair remains disabled when optional arrays are absent.

## Repair Loss Changes

Reuse the branch-weighted old-key surrogate from M368, but apply it to gap-tail
rows as balanced retention rather than single hard-row rejection pressure:

```text
L_old_key =
  preferred_branch_weight * L_source_preference
+ wrong_branch_weight * L_wrong_preference
+ lambda_anchor * (
     preferred_branch_weight * preferred_action_anchor
   + wrong_branch_weight * rejected_action_anchor
  )
```

For gap-tail rows, the purpose is to keep the promoted alpha `0.4` margin-gap
lower tail from eroding while allowing movement on non-tail rows. This is still
only a proxy; closed-loop old-key replay must decide acceptance.

## Acceptance Order

M373 should only implement and test the gap-tail overlay path. M374 should
probe it without PPO:

1. export a gap-tail overlay from M371 rows;
2. rebuild the old-key preference corpus with hard-row and gap-tail overlays;
3. run exact repair from alpha `0.6` or the M369 repaired endpoint;
4. run old-key targeted replay and replay-gate adapter;
5. if old-key passes beyond alpha `0.4`, run source-diverse and first replay
   gates;
6. do not promote directly.

If the weighted surrogate improves exact metrics but still erodes gap p10, then
classify it as `metric_artifact` / `objective_overfit` and consider a
trajectory-level terminal-margin residual. Do not relax the old-key gate.

## Decision

Admit:

```text
m373-old-key-gap-tail-feedback-implementation
```

Decision:

```text
admit_m373_old_key_gap_tail_feedback_implementation
```
