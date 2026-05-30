# M1704 Paper-Route Controller-Family Bounded Calibration Smoke Design

- status: completed
- decision: `bounded_calibration_smoke_design_admit_no_rollout_subset_preflight`
- parent audit: `docs/m1703-paper-route-controller-family-task-quality-calibration-preflight-result-audit.md`
- full matrix: `runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv`

## Summary

M1704 designs a bounded diagnostic calibration smoke from the M1702 matrix.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Problem

M1702 produced a clean metadata matrix:

```text
72 base specs * 12 calibration variants * 12 profiles = 10368 cells
```

The matrix is valid, but directly executing all cells would be premature. The
current branch is trying to answer a task-quality question first:

```text
Do track-width, finish, and max-step calibration axes make outcome buckets
interpretable enough to support later controller-family comparisons?
```

That is different from ranking controllers.

## Bounded Smoke Scale

M1705 should materialize a no-rollout subset with this shape:

```text
selected base specs: 6
calibration variants per base spec: 12
profiles per calibration spec: 12
total cells: 6 * 12 * 12 = 864
```

This keeps the execution budget equal to the already-tested M1693/M1698
864-episode public rollout scale while reducing the calibration matrix from
`10368` to `864` cells.

## Source Selection Rule

M1705 should deterministically select six base specs from the M1702 matrix:

```text
T4: 3 base specs
T5: 3 base specs
```

Within each task family, prefer distinct:

```text
source_edge;
executable_source_family;
env_template_family;
window_tag.
```

If multiple candidates tie, use stable lexical ordering by `base_task_source_id`
after applying source-diversity caps. The selector must write the selected base
specs and rejected candidate reasons so the subset is auditable.

## Calibration Variants

For each selected base spec, keep the full calibration axis product:

| axis | values |
| --- | --- |
| `track_width_scale` | `1.0`, `1.5`, `2.0` |
| `finish_variant` | `original`, `relaxed` |
| `max_steps_scale` | `1.0`, `1.5` |

This produces `12` calibration variants per selected base spec. Dropping an axis
inside the smoke would make the task-quality question underdetermined.

## Profile Controls

Every selected calibration spec must keep all twelve controller-family profiles:

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

The smoke should aggregate first by calibration variant across profiles. Profile
rows are controls and diagnostics, not ranking evidence.

## Required Metrics For Later Execution

A later execution should report outcome-conditional metrics by:

```text
track_width_scale;
finish_variant;
max_steps_scale;
task_family;
source_edge;
profile_name.
```

Required metrics:

```text
episode_count
success_obstacle_pass_rate
collision_failure_rate
off_track_noncollision_noncompletion_rate
max_steps_noncompletion_rate
safe_noncollision_noncompletion_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
termination_reason_histogram
```

The first interpretation layer must be task-quality:

```text
Did wider track reduce off-track dominance?
Did relaxed finish reduce noncompletion without hiding collision?
Did longer max steps turn timeouts into interpretable pass/fail outcomes?
```

Only after a later audit says outcome modes are interpretable can the branch
consider controller-family comparisons.

## Smoke Acceptance Logic

Execution of this smoke, if later admitted, should be judged as diagnostic:

```text
Pass plumbing:
  zero runner failures
  finite selected metrics
  zero guardrail violations
  outcome aggregates present

Admit next calibrated execution design:
  at least one calibration variant reduces off-track dominance enough that
  obstacle-pass and collision-failure rates become interpretable

Route to task repair:
  all calibration variants remain off-track dominated
  or source selection produces too few task/source families
  or profile rows become invalid/missing
```

The smoke must not promote a controller, rank profiles, use private holdout, or
claim finite-window history necessity.

## M1705 Preflight Artifacts

The next milestone should materialize the subset without rollout:

```text
runs/m1705_controller_family_bounded_calibration_smoke_preflight/summary.json
runs/m1705_controller_family_bounded_calibration_smoke_preflight/selected_base_specs.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/rejected_base_specs.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_calibration_specs.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_smoke_matrix.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/contract_violations.csv
```

Expected no-rollout counts:

```text
selected base specs: 6
bounded calibration specs: 72
bounded smoke matrix cells: 864
contract violations: 0
environment rollout started: false
```

## Guardrails

Forbidden:

```text
direct full 10368-cell execution;
profile-specific tuning;
controller-family ranking;
private holdout use;
actor input changes;
training / replay / PPO / promotion;
dropping L1/L2-current-tiled/L3-online/L3-reset controls.
```

Allowed:

```text
no-rollout subset materialization;
source-diverse deterministic selection;
outcome-conditional metric definitions;
later bounded public execution design after preflight audit.
```

## Decision

Admit M1705 no-rollout bounded calibration smoke subset preflight. Do not execute
the smoke until the subset is materialized, audited, and explicitly routed to a
measured execution milestone.
