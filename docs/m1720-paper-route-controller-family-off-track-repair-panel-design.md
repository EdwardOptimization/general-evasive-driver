# M1720 Paper-Route Controller-Family Off-Track Repair Panel Design

- status: completed
- decision: `off_track_repair_panel_design_admit_no_rollout_preflight`
- parent audit: `docs/m1719-paper-route-controller-family-off-track-dominance-localization-result-audit.md`

## Summary

M1720 designs a fixed-budget off-track repair panel from M1718 localized target
slices.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, rank
controller families, or claim paper-level evidence or level3 self-identification.

## Design Goal

M1716 found a conditional-positive task-quality scale-up, but off-track remained
dominant. M1718/M1719 localized enough structure to justify repair design, not a
source-distribution reset.

The repair panel should answer:

```text
Can a targeted task-quality panel reduce off-track dominance on localized repair
slices while preserving collision controls and public diagnostic profile rows?
```

It should not answer:

```text
Which controller-family profile is best?
```

## Fixed-Budget Shape

M1721 should materialize a no-rollout repair panel:

```text
selected base specs: 18
target task split: T4=12, T5=6
repair variants per base spec: 4
profiles: 12
total cells: 18 * 4 * 12 = 864
```

The `T4=12`, `T5=6` split intentionally emphasizes T4 because M1718 localized
more source-task and variant-task repair targets there, while retaining T5
coverage because T5 target slices remain present.

## Source Selection Rule

M1721 should select base specs only from sources traceable to M1718 target
slices.

Use this deterministic source rule:

```text
1. Load M1718 repair_target_slices.csv.
2. Use only non-profile target slices:
   - variant_source_edge
   - variant_task_family
   - source_task_family
3. Map target source_edge/task_family pairs back to eligible M1702 base specs.
4. Select 12 T4 and 6 T5 base specs by greedy source diversity.
5. Prioritize higher off-track rate, lower collision rate, then distinct
   source_edge, executable_source_family, env_template_family, and window_tag.
6. Break remaining ties lexically by base_task_source_id.
```

The selector must not use profile success, profile return, profile rank, or any
controller-family comparison metric.

If the target set cannot supply enough T4/T5 sources, M1721 should stop and
route to source-distribution redesign instead of silently filling from unrelated
sources.

## Repair Variant Panel

Every selected base spec should keep four variants:

| label | track width | finish | max steps | reason |
| --- | ---: | --- | ---: | --- |
| `original_axis_baseline` | `1.0` | `original` | `1.0` | preserves baseline |
| `best_off_track_variant` | `2.0` | `original` | `1.5` | M1716 conditional-positive control |
| `collision_control_wide_relaxed` | `2.0` | `relaxed` | `1.0` | M1716 conditional-positive collision guard |
| `wide_relaxed_extended` | `2.0` | `relaxed` | `1.5` | missing composite repair candidate |

The missing composite variant is available in the M1702 calibration matrix:

```text
track_width_scale=2.0
finish_variant=relaxed
max_steps_scale=1.5
```

M1721 must verify availability before materializing the panel. If the composite
variant is unavailable for a selected base spec, the preflight should fail
rather than substitute another variant.

## Required Controls

Every selected repair spec must keep all twelve controller-family profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Profile rows remain controls. M1721 and later audits must not rank profiles.

## M1721 Preflight Artifacts

M1721 should write:

```text
runs/m1721_off_track_repair_panel_preflight/summary.json
runs/m1721_off_track_repair_panel_preflight/selected_base_specs.csv
runs/m1721_off_track_repair_panel_preflight/rejected_target_sources.csv
runs/m1721_off_track_repair_panel_preflight/repair_panel_specs.json
runs/m1721_off_track_repair_panel_preflight/repair_panel_specs.csv
runs/m1721_off_track_repair_panel_preflight/repair_panel_matrix.csv
runs/m1721_off_track_repair_panel_preflight/contract_violations.csv
```

Expected no-rollout counts:

```text
selected base specs: 18
selected task family counts: T4=12, T5=6
repair panel specs: 72
repair panel matrix cells: 864
profile count: 12
contract violations: 0
environment rollout started: false
```

## Later Execution Audit Rules

A later execution audit should compare the new `wide_relaxed_extended` variant
against:

```text
original_axis_baseline
best_off_track_variant
collision_control_wide_relaxed
```

The repair should be considered useful only if it reduces off-track dominance on
the selected repair panel without exceeding the collision guard. Exact execution
thresholds should be pre-registered after M1721/M1722 confirm the preflight
shape.

## Claim Boundary

Allowed:

```text
off-track repair panel design;
no-rollout preflight route.
```

Forbidden:

```text
rollout result;
controller-family ranking;
recurrent advantage;
finite-window history necessity;
private-holdout evidence;
paper-level evidence;
level3 self-identification.
```

## Decision

Admit M1721 no-rollout repair panel preflight. Do not execute the repair panel
until the subset is materialized, audited, and explicitly routed to measured
execution design.
