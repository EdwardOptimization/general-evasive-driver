# M1701 Paper-Route Controller-Family Task-Quality Calibration Design

- status: completed
- decision: `task_quality_calibration_design_admit_no_rollout_preflight`
- parent synthesis: `docs/m1700-paper-route-controller-family-outcome-semantics-branch-synthesis.md`
- new branch: `paper_route_controller_family_task_quality_calibration`

## Summary

M1701 designs a calibrated task-quality route after M1700 showed that the
current controller-family workload is off-track dominated.

This milestone is design-only. It does not execute rollout, train, replay, run
PPO, promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Problem

M1698 separated outcome semantics and found:

```text
success_obstacle_pass: 32
collision_failure: 38
off_track_noncollision_noncompletion: 794
```

Raw success is therefore not a fair controller-family comparison metric. The
current workload mostly measures road-boundary survival before it measures
obstacle-avoidance quality.

## Calibration Goal

Build a public calibrated evaluation protocol that separates:

```text
obstacle pass
obstacle collision
off-track termination
max-step noncompletion
other termination
```

The goal is not to make the task easy. The goal is to make the outcome modes
interpretable enough that later controller-family comparisons do not conflate
boundary failure with obstacle avoidance.

## Required Metrics

Every calibrated rollout aggregate should include:

```text
obstacle_pass_rate
collision_failure_rate
off_track_rate
max_steps_noncompletion_rate
safe_noncollision_noncompletion_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
```

Controller comparisons must be conditional:

```text
compare pass rates only within matched scenario strata;
compare collision and off-track rates separately;
report off-track-dominated strata as task-quality failures, not controller wins;
keep L1, L2-current-tiled, L3-online, and L3-reset controls together.
```

## Calibration Axes

M1702 should materialize a no-rollout calibration matrix with these axes:

| Axis | Values | Purpose |
| --- | --- | --- |
| `track_width_scale` | `1.0`, `1.5`, `2.0` | distinguish obstacle failure from strict road-boundary failure |
| `finish_pass_distance` | original, relaxed | check whether completion semantics are too strict |
| `max_steps_scale` | `1.0`, `1.5` | distinguish true failure from timeout before completion |
| `source_family` | existing M1690 families | preserve task-source stratification |
| `task_family` | `T4`, `T5` | preserve capability and obstacle families |

The preflight should not execute environment rollout. It should only write the
calibration matrix and verify that every generated env config preserves P0
human-view/no-wheel/no-oracle actor inputs.

## Artifact Plan

M1702 should write:

```text
runs/m1702_controller_family_task_quality_calibration_preflight/summary.json
runs/m1702_controller_family_task_quality_calibration_preflight/calibration_specs.json
runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv
runs/m1702_controller_family_task_quality_calibration_preflight/profile_artifacts.csv
runs/m1702_controller_family_task_quality_calibration_preflight/contract_violations.csv
```

Expected scale:

```text
base executable specs: 72
profiles: 12
track width variants: 3
finish variants: 2
max-step variants: 2
raw matrix cells before later pruning: 72 * 12 * 3 * 2 * 2 = 10368
```

M1702 may materialize the full matrix as metadata but must not execute it. A
later design should select a bounded public smoke before any large rerun.

## Guardrails

Forbidden:

```text
profile-specific tuning;
controller-family ranking from M1698;
private holdout use;
actor input changes;
training / replay / PPO / promotion;
using calibration failure to tune one profile;
dropping L1/L2-current-tiled/L3-reset controls.
```

Allowed:

```text
logging-only calibration metadata;
P0-compatible env config variants;
outcome-conditional metric definitions;
source/spec stratification;
later bounded public smoke design.
```

## Decision

Admit M1702 no-rollout task-quality calibration preflight. Do not execute the
calibration matrix or claim controller-family ranking until a later calibrated
audit says the outcome modes are interpretable.
