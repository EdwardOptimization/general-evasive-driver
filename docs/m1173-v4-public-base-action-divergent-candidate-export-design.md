# M1173 V4 Public Base Action-Divergent Candidate Export Design

## Purpose

M1173 designs a filtered, score-balanced candidate export for the
`stronger_wrong_history_construction` branch.

This milestone is design-only. It does not run replay, run mining, train actor
weights, run PPO, promote, use private holdout, convert rows, or change actor
inputs.

## Why Export Is Needed

M1172 found useful candidate signal in existing artifacts, but direct proof
conversion is not justified:

```text
combined hard filter:
  rows: 151
  physical pairs: 8
  checkpoints: 6
  targets: 2

normal_better rows:
  rows: 36
  physical pairs: 2
```

The export should avoid two failures:

```text
unfiltered M1161 outcome CSV:
  too broad; action-divergent signal is diluted.

strict normal_better/high-margin filter:
  too narrow; collapses toward old active-set pairs.
```

## Candidate Pool Rule

Use existing M1161 `wrong_matched_history` rows only:

```text
margin_gap >= 0.0025
and (
  first_action_distance >= 0.15
  or action_trajectory_distance_mean >= 0.06
)
```

Read-only count on existing artifacts:

```text
pool rows: 343
physical pairs: 17
targets: 3
checkpoints: 6
left steps: 9
max pair fraction: 0.069971
```

This pool is broad enough for a diagnostic export while still requiring
terminal-margin sensitivity and action divergence.

## Score

Rank rows by:

```text
score =
  first_action_distance / 0.25
  + action_trajectory_distance_mean / 0.15
  + max(margin_gap, 0) / 0.01
  + 0.25 * target_z_delta
  - visible_distance / 0.25
```

This is not a training loss. It is a candidate ordering for source-balanced
export.

## Export Gate

The exporter should write a filtered outcome CSV and a summary:

```text
max exported rows: 240
min physical pairs: 12
min targets: 3
min checkpoints: 6
min left steps: 6
max pair fraction: 0.15
required variant: wrong_matched_history
input: M1161 outcome_interventions.csv
```

The output is still not a proof corpus. It is only an input for a later bounded
relocation replay diagnostic.

## Tooling Route

The existing relocation runner can replay from an `outcome_csv`, but it does
not apply action-divergence filters inline. Therefore M1174 should implement or
add a small exporter that:

1. reads `outcome_interventions.csv`;
2. filters with the M1173 pool rule;
3. computes the score;
4. applies source-balanced row selection;
5. writes `candidate_outcomes.csv` and `summary.json`.

M1174 should not run replay. Replay should be a separate milestone after the
export is audited.

## Guardrail

No replay, mining, actor training, PPO, promotion, private holdout, conversion,
threshold weakening, or actor-input change occurred.

## Decision

```text
decision: action_divergent_candidate_export_design_admit_export_tooling
next: m1174-v4-public-base-action-divergent-candidate-export-tooling
```
