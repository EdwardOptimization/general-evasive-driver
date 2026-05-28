# M1179 V4 Public Base Stronger Wrong-History Construction Synthesis

## Purpose

M1179 synthesizes the `stronger_wrong_history_construction` branch after
M1171-M1178.

This is a workflow synthesis milestone. It does not run mining, run replay,
train actor weights, run PPO, promote, use private holdout, convert failed
surface rows, or change actor inputs.

## Evidence Summary

The branch started from the M1170 finding:

```text
same-shape wrong-history relocation recovered only the old two-pair active set.
```

M1171 proposed a stronger wrong-history construction based on:

```text
action divergence
terminal-margin sensitivity
source diversity
current-frame match guard
actor contract guard
```

M1172 found useful signal in existing M1161 artifacts:

```text
wrong_matched_history rows: 4585
first_action_distance >= 0.20: 630 rows, 30 physical pairs
margin_gap >= 0.005: 204 rows, 12 physical pairs
normal_better == true: 36 rows, 2 physical pairs
```

This supported a candidate export, but not proof conversion.

M1175 exported an action-divergent candidate set:

```text
candidate_pool_rows: 343
selected_rows: 240
selected_physical_pairs: 17
selected_left_steps: 9
selected_targets: 3
selected_checkpoints: 6
max_selected_pair_fraction: 0.0625
success_drop_rows: 0
```

M1177 ran bounded relocation on that candidate set:

```text
source_budget_ready: true
relocation_replay_started: true
raw_rows: 1054
raw_accepted_wrong_rows: 78
balanced_accepted_wrong_rows: 38
accepted_wrong_physical_pairs: 2
accepted_wrong_targets: 1
accepted_wrong_normal_margin_buckets: 1
max_rows_per_physical_pair_fraction: 0.5263157895
```

M1178 confirmed the accepted physical pairs exactly match M1169:

```text
116117:36:116124:15
116117:39:116124:15
```

and found that the artifact-only candidate table cannot balance source obstacle
geometry:

```text
source_obstacle_bucket: x=nan|y=nan for all M1175 selected rows
```

## Supported Claims

Existing M1161 artifacts contain action-divergent wrong-history signal.

The deterministic exporter and bounded relocation path are reproducible and
guarded by source-diversity criteria.

Action-divergent filtering increases the accepted row count on the old active
set:

```text
M1169 accepted rows: 6
M1177 raw accepted rows: 78
M1177 balanced accepted rows: 38
```

The current public-gate base still has real wrong-history boundary sensitivity
on a small active set.

## Falsified Claims

The branch falsifies these working claims:

```text
M1161 artifact-only action-divergent filtering is sufficient to discover a broad source-diverse wrong-history surface.
```

```text
High action-divergent score alone predicts relocation-materializable source-diverse wrong-history rows.
```

```text
Continuing to rescore or rerun bounded relocation on the same M1161 outcome table is the next highest-leverage move.
```

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  accepted wrong-history rows remain concentrated in two physical pairs and one target.

metric_artifact:
  action-divergent score is a useful candidate signal, but not a proof-surface predictor.

public_gate_overfit_risk:
  repeated artifact-only work keeps returning to the same old active set.
```

This branch did not expose a source-budget failure, runtime failure, actor
contract violation, training instability, PPO issue, private holdout issue, or
checkpoint-promotion issue.

## Public Gate Overfit Risk

The project is now at risk of repeatedly optimizing around:

```text
116117:36:116124:15
116117:39:116124:15
future_yaw_response
normal_margin around 0.0017 to 0.0025
```

These rows are useful protected diagnostics, but not enough to support a broad
self-identification or driver capability claim.

## Next Branch Decision

Close:

```text
stronger_wrong_history_construction
```

Open:

```text
source_rich_extreme_scenario_surface_refresh
```

The next branch should not keep replaying the same M1161 outcome table. It
should generate or refresh source-rich data that records:

```text
source obstacle body geometry
target obstacle body geometry
fault family and fidelity class
fault onset bucket
warm-up/probing mode
hidden dynamics severity
current-frame match metrics
action divergence metrics
terminal margin sensitivity
```

This matches the earlier extreme hidden-dynamics route lessons from M824-M831:
extreme/fault scenarios are useful, but current-model faults, proxy faults, and
future-only wheel-level faults must stay separated.

The first milestone in the new branch should be design-only. It should decide
how to refresh source-rich extreme scenario coverage under the current public
base, and it should explicitly avoid treating wheel blowout, split-mu, stuck
caliper, halfshaft loss, or wheel-speed sensor faults as current-model physical
evidence unless the simulator is extended to represent them.

## Guardrail

No mining, replay, actor training, PPO, promotion, private holdout, failed-row
conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: stronger_wrong_history_construction_synthesis_pivot_to_source_rich_extreme_scenario_surface_refresh
next: m1180-v4-public-base-source-rich-extreme-scenario-refresh-design
```
