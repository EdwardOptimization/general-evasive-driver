# M367 Old-Key Hard-Row Weighting Design

M367 designs how old-key replay regressions feed back into the differentiable
old-key repair corpus. It does not run PPO, promote a checkpoint, lower
closed-loop old-key replay thresholds, or change actor inputs.

## Problem

M365 promoted:

```text
runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
```

M366 found the first failing tested interpolation, alpha `0.2`, fails only one
old-key compact row:

```text
9951|perturbed|35|32|10.000000|-1.200000|1.400000
```

The normal-history branch does not regress. The failure is a wrong-history
terminal-margin sign crossing:

| Policy | Wrong-history margin |
| --- | ---: |
| m360_base | -0.000000094854 |
| m364a_0_1 | -0.000000015094 |
| m364a_0_2 | +0.000000087150 |

This means the current old-key surrogate is not sufficiently protecting
wrong-history failure on rows with almost zero rejected-branch margin slack.

## Design Principle

Closed-loop old-key replay remains authoritative. The differentiable corpus is a
repair guide, not the proof gate.

The hard-row feedback path should:

- mark replay-discovered accepted regressions as `hard_row`;
- increase the weight of wrong-history preference and rejected-action anchoring
  for hard rows;
- include wrong-history margin slack metadata;
- preserve the same deployable student inputs:
  `observation`, `preferred_hidden`, `rejected_hidden`;
- keep all hidden dynamics, oracle labels, and high-level feasibility labels out
  of the actor.

## Hard-Row Overlay Schema

Create an optional CSV overlay consumed by `old_key_preference_corpus`:

```text
case_id
hard_row
hard_row_reason
hard_weight_multiplier
wrong_branch_weight_multiplier
preferred_branch_weight_multiplier
reference_wrong_history_margin
candidate_wrong_history_margin
candidate_accepted_regression
```

For M366, the row should be:

```text
case_id = 9951|perturbed|35|32|10.000000|-1.200000|1.400000
hard_row = true
hard_row_reason = wrong_history_margin_sign_crossing
hard_weight_multiplier = 8.0
wrong_branch_weight_multiplier = 16.0
preferred_branch_weight_multiplier = 1.0
reference_wrong_history_margin = -0.000000094854
candidate_wrong_history_margin = +0.000000087150
candidate_accepted_regression = true
```

The multipliers are training-time metadata only. They must not enter the
deployable actor observation.

## Corpus Changes

Extend `old_key_preference_corpus.py` to:

1. compute a stable `case_id` for each compact row;
2. optionally load a hard-row overlay CSV;
3. merge overlay fields by `case_id`;
4. multiply the base row weight by `hard_weight_multiplier`;
5. write the following metadata fields:

```text
case_id
hard_row
hard_row_reason
hard_weight_multiplier
wrong_branch_weight_multiplier
preferred_branch_weight_multiplier
reference_wrong_history_margin
candidate_wrong_history_margin
candidate_accepted_regression
```

The NPZ should add optional arrays:

```text
hard_row
wrong_branch_weight
preferred_branch_weight
```

Existing loaders must remain backward-compatible. If these arrays are absent,
the repair loss should behave exactly as before.

## Repair Loss Changes

Extend old-key surrogate computation with per-row branch weights:

```text
L_old_key =
  preferred_branch_weight * L_source_preference
+ wrong_branch_weight * L_wrong_preference
+ lambda_anchor * (
     preferred_branch_weight * preferred_action_anchor
   + wrong_branch_weight * rejected_action_anchor
  )
```

For a hard row caused by wrong-history margin sign crossing, the main pressure
should be on:

```text
wrong_branch_weight
rejected_action_anchor
wrong_preference
```

The goal is not to make the policy merely different. The goal is to keep
wrong-history closed-loop behavior on the unsafe side of the old-key boundary
while retaining normal-history success.

## Acceptance Order

M368 should only implement and test the hard-row corpus path. M369 should probe
it without PPO:

1. export hard-row overlay from M366 comparison rows;
2. rebuild old-key preference corpus with hard-row weights;
3. run exact repair with the weighted old-key corpus;
4. run old-key targeted replay;
5. if old-key passes at alpha above `0.1`, run source-diverse and first replay
   gates;
6. do not promote directly.

If alpha `0.2` still fails by the same row, classify it as `objective_overfit`
and consider adding a terminal-margin classifier or value residual. Do not
lower old-key replay thresholds.

## Decision

Admit:

```text
m368-old-key-hard-row-feedback-implementation
```

Decision:

```text
admit_m368_old_key_hard_row_feedback_implementation
```
