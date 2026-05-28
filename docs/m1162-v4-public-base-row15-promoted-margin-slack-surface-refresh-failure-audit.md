# M1162 V4 Public Base Row15 Promoted Margin-Slack Surface Refresh Failure Audit

## Purpose

M1162 audits the M1161 margin-slack surface refresh failure before any rerun,
threshold change, conversion, PPO, or promotion.

This milestone reads existing M1161 artifacts only.

## Source Budget Was Not The Blocker

Matched-current mining produced a broad candidate pool:

```text
accepted_pair_count: 4585
accepted_physical_pair_count: 242
accepted_left_step_count: 27
accepted_source_obstacle_bucket_count: 24
accepted_by_target:
  future_braking_deceleration: 1600
  future_lateral_accel_response: 1600
  future_yaw_response: 1385
```

The outcome gate and candidate selection also had enough raw material:

```text
outcome_row_count: 27510
outcome_summary_rows: 108
source_budget_ready: true
selected_rows: 1200
selected_physical_pairs: 242
selected_left_steps: 27
selected_targets: 3
max_selected_pair_fraction: 0.004167
```

So M1161 did not fail because the six-policy family could not produce matched
current candidates.

## Relocation Collapsed The Surface

Final relocation produced:

```text
raw relocation rows: 21250
accepted rows across all variants: 1710
balanced wrong-history exportable rows: 15
accepted wrong-history physical pairs: 2
accepted wrong-history left steps: 2
accepted wrong-history checkpoints: 2
accepted wrong-history targets: 1
accepted wrong-history normal-margin buckets: 1
accepted wrong-history normal-margin max: 0.002483
max rows per physical pair fraction: 0.666667
```

The accepted wrong-history rows are only:

```text
row15_current / future_yaw_response: 10 rows
row15_previous_alpha015 / future_yaw_response: 5 rows
```

They come from two physical pairs:

```text
116117:39:116124:15 -> 10 rows
116117:36:116124:15 -> 5 rows
```

## Wrong-History Sensitivity Is Sparse In This Refresh

Across `4250` relocated `wrong_matched_history` rows:

```text
accepted wrong-history rows: 15
balanced exportable rows: 15
normal success + wrong-history success: 4086
normal success + wrong-history failure: 15
normal failure rows: 149
```

Accepted wrong-history rows are also low-slack:

```text
normal_margin_min: 0.001947
normal_margin_mean: 0.002295
normal_margin_max: 0.002483
margin_gap_mean: 0.002516
```

By contrast, the relocation produced many accepted reset/zero-current response
rows before final wrong-history balancing:

```text
accepted reset rows: 1010
accepted zero-current-response rows: 655
accepted wrong-history rows: 15
```

This means the current task family still contains response-ablation sensitivity,
but this specific wrong-matched-history intervention does not produce a broad
fresh wrong-history surface under the M1160 relocation search.

## Failure Classification

Not supported:

```text
source_budget_shortfall
training_instability
contract_violation
private_holdout_contamination
threshold weakening needed before audit
```

Supported classification:

```text
relocation_active_set_collapse
wrong_history_intervention_scarcity
duplicate_dominated_boundary_surface
margin_slack_shortfall
```

The failure is best described as:

```text
M1161 found many matched candidates and many response-ablation-sensitive rows,
but wrong-matched-history success drops remained rare after relocation and
collapsed into two low-slack yaw-response physical pairs.
```

## Next Route

Do not convert M1161 and do not lower the acceptance thresholds.

The next step should design a relocation-expansion diagnostic using the existing
M1161 outcome CSV. This should keep the M1160 acceptance thresholds but expand
the relocation search, for example by:

```text
using more candidate rows from the existing outcome CSV
adding body longitudinal/lateral offsets
optionally adding bounded half-width inflation variants
keeping wrong-history-specific acceptance and source diversity gates
```

This tests whether M1161 failed because the relocation search was too narrow,
without re-mining source pairs or weakening the proof gate.

## Decision

```text
decision: row15_promoted_margin_slack_failure_audit_route_to_relocation_expansion_design
next: m1163-v4-public-base-row15-promoted-relocation-expansion-design
```
