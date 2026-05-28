# M1170 V4 Public Base Row15 Promoted Margin-Slack Surface Refresh Synthesis

## Purpose

M1170 synthesizes the `row15_promoted_margin_slack_surface_refresh` branch
after M1160-M1169.

This is a synthesis milestone. It does not run mining, run replay, train actor
weights, run PPO, promote, use private holdout, convert failed surface rows, or
change actor inputs.

## Evidence Summary

The branch started after M1158 promoted:

```text
current public-gate base:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

The branch objective was to refresh current-base source-diverse wrong-history
surfaces with more margin slack before any PPO continuation.

Key results:

```text
M1161 source budget:
  matched-current accepted pairs: 4585
  physical pairs: 242
  left steps: 27
  selected rows before relocation: 1200
  selected physical pairs: 242

M1161 final relocation:
  accepted wrong-history rows: 15
  physical pairs: 2
  targets: 1
  normal-margin buckets: 1
  normal-margin max: 0.002483

M1162 audit:
  accepted reset rows before final balancing: 1010
  accepted zero-current rows before final balancing: 655
  accepted wrong-history rows: 15
  conclusion: response-ablation sensitivity exists, but wrong-matched-history
  relocation is sparse.

M1164 expansion:
  interrupted after roughly 33 minutes with no summary artifact.

M1166 staged pilot:
  selected rows: 240
  selected physical pairs: 240
  accepted wrong-history rows: 1
  accepted physical pairs: 1

M1167 audit:
  M1166 selected both old M1161 accepted pairs.
  M1166 omitted the fine 0.0005 target-margin value.
  failure is target-grid artifact plus broader wrong-history scarcity.

M1169 microgrid:
  accepted wrong-history rows: 6
  accepted physical pairs: 2
  new physical pairs beyond M1161: 0
```

## Supported Claims

The source budget is not the blocker. The branch repeatedly had hundreds of
eligible physical pairs and broad left-step coverage before relocation.

Fine target margins matter. Restoring fine target margins recovered both old
M1161 accepted physical pairs.

Same-shape relocation can recover the old active set, but it does not reveal a
broad source-diverse wrong-history surface under the current public base.

Reset/zero-current interventions remain much stronger than wrong-matched
history, which suggests the actor is sensitive to explicit response ablations,
but the current wrong-history construction is not strong enough or not aligned
enough to produce broad terminal failures.

## Falsified Claims

The branch falsifies this claim:

```text
alpha_0_05 has a broad source-diverse wrong-history margin-slack surface under
the current same-shape relocation construction.
```

It also weakens these routes:

```text
larger same-shape relocation expansion will solve the surface shortage
body-offset expansion is the next highest-leverage move
M1166 failed only because of target-margin grid coarseness
```

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  the accepted wrong-history surface collapses to two old physical pairs.

metric_artifact:
  M1166 undercounted the old active set because its target-margin grid omitted
  the fine 0.0005 value.
```

This is not a source-budget failure, not a private-holdout issue, not a
contract violation, and not a PPO/training instability.

## Public Gate Overfit Risk

The current public proof surface is at risk of overfitting to a tiny old active
set:

```text
accepted physical pairs after microgrid: 2
new physical pairs beyond M1161: 0
normal-margin bucket count: 1
target count: 1
checkpoint count: 1
```

Converting this into an objective corpus or using it for PPO retention would
mostly teach the actor about the same old near-boundary rows.

## Next Branch Decision

Close:

```text
row15_promoted_margin_slack_surface_refresh
```

Open:

```text
stronger_wrong_history_construction
```

The next branch should design a stronger wrong-history intervention
construction before any more relocation expansion or PPO. It should directly
target the issue seen here:

```text
normal branch succeeds;
wrong-history branch also succeeds too often.
```

The next design should prefer wrong histories that are action-divergent,
capability-divergent, and terminal-margin-sensitive, instead of only
source-balanced matched-current histories.

## Guardrail

No mining, replay, actor training, PPO, promotion, private holdout, failed-row
conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: row15_promoted_margin_slack_surface_refresh_synthesis_pivot_to_stronger_wrong_history_construction
next: m1171-v4-public-base-stronger-wrong-history-construction-design
```
