# M1169 V4 Public Base Row15 Promoted Relocation Target Microgrid Run

## Purpose

M1169 ran the target-margin microgrid diagnostic designed in M1168.

The diagnostic reused the existing M1161 outcome CSV, restored fine
near-boundary target margins including `0.0005`, kept body offsets fixed at
`0.0`, and evaluated only `wrong_matched_history`.

It did not rerun mining, rerun the outcome gate, train actor weights, run PPO,
promote, use private holdout, convert a surface, weaken thresholds, or change
actor inputs.

## Result

```text
summary:
  runs/m1169_row15_promoted_target_microgrid_seed116100/summary.json

source_budget_ready: true
candidate wrong-history rows: 4585
eligible physical pairs: 242

selected rows: 240
selected physical pairs: 240
selected left steps: 27
selected targets: 3

raw relocation rows: 848
accepted wrong-history rows: 6
accepted wrong-history physical pairs: 2
accepted wrong-history left steps: 2
accepted wrong-history checkpoints: 1
accepted wrong-history targets: 1
accepted wrong-history normal-margin buckets: 1
accepted wrong-history normal-margin min: 0.001708
accepted wrong-history normal-margin max: 0.002483
max rows per physical pair fraction: 0.666667
control accepted wrong-history rows: 0
decision: reject_duplicate_dominated_boundary_surface
passed: false
```

All accepted rows are `row15_current/future_yaw_response` and come from the two
known M1161 physical pairs:

```text
116117:36:116124:15
116117:39:116124:15
```

## Comparison

```text
M1161:
  accepted wrong-history rows: 15
  accepted physical pairs: 2
  accepted normal-margin max: 0.002483

M1166:
  accepted wrong-history rows: 1
  accepted physical pairs: 1
  accepted normal-margin max: 0.002457

M1169:
  accepted wrong-history rows: 6
  accepted physical pairs: 2
  accepted normal-margin max: 0.002483
```

M1169 confirms that M1166 was partly a target-grid false negative: restoring
fine target margins recovers the second old M1161 physical pair.

But the diagnostic does not reveal a broader source-diverse wrong-history
surface. It recovers only the old two physical pairs and remains
duplicate-dominated.

## Interpretation

This settles the immediate target-grid question:

```text
fine target margins matter: true
old M1161 physical pairs recovered: true
new physical pairs beyond M1161: 0
same-shape relocation expansion justified: false
```

The branch should not continue by increasing candidate count or body-offset
cross products. The evidence now points to a stronger wrong-history
construction problem: the current wrong-matched-history intervention is too
often safe once the normal branch is safe.

## Guardrail

No mining, outcome rerun, actor training, PPO, promotion, private holdout,
surface conversion, threshold weakening, or actor-input change occurred.

## Decision

Route to branch synthesis. The synthesis should close
`row15_promoted_margin_slack_surface_refresh` and decide the next branch,
likely a stronger wrong-history construction or intervention design.

```text
decision: row15_promoted_target_microgrid_recovers_old_pairs_route_to_branch_synthesis
next: m1170-v4-public-base-row15-promoted-margin-slack-surface-refresh-synthesis
```
