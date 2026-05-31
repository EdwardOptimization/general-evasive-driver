# M2028 Paper-Route T2/T3 Source Generation Design

- status: completed
- decision: `t2_t3_source_generation_design_admit_no_rollout_preflight_implementation`
- blocker source: `docs/m2027-paper-route-controlled-comparison-source-coverage-repair-result-audit.md`
- governing plans:
  - `docs/self-id-go-no-go-paper-route-plan.md`
  - `docs/paper-route-finite-window-vs-gru-plan.md`
- reset/rollout/measured execution in M2028: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2028 designs the next branch after the M2027 pivot: generate new
source-diverse T2/T3 same-family panel rows before any routing smoke. The goal
is not to prove controller performance. The goal is to make the controlled
comparison panel fair enough that a future routing smoke would not overfit to
already-ready families.

The design follows two governing constraints:

```text
1. Self-ID / GRU belief remains a bounded hypothesis, not the assumed winner.
2. T2/T3 are the task families most relevant to finite-window-vs-GRU and
   history-dependence claims, so they cannot be skipped by running only the
   ready T1/T4/T5 families.
```

## Current T2/T3 State

From M2026 repaired panel sources:

```text
T2_same_current_different_older_history:
  total rows: 36
  source_kind counts:
    actuator_delay_proxy+capability_step_proxy: 21
    actuator_delay_proxy: 5
    capability_step_proxy: 5
    capability_step_proxy+warmup_proxy: 5
  max single source-kind share: 21/36 = 0.5833

T3_active_diagnostic_warmup:
  total rows: 24
  source_kind counts:
    actuator_delay_proxy+terminal_boundary_proxy+warmup_proxy: 9
    capability_step_proxy+terminal_boundary_proxy+warmup_proxy: 9
    capability_step_proxy+warmup_proxy: 5
    terminal_boundary_proxy+warmup_proxy: 1
  max single source-kind share: 9/24 = 0.3750
```

Registered readiness target:

```text
source_count >= 12
max_single_source_kind_share <= 0.35
```

M2026 fixed T1 but found no clean existing same-family top-up for T2/T3.
Therefore M2028 does not lower the threshold or relabel ready-family rows.

## Design Principle

Generate source rows with slack:

```text
do not edge-pass the source-kind gate;
generate enough new non-dominant rows that one future rejected row does not
make the family unready again.
```

For T2, if the current dominant count of 21 is retained, the strict minimum
total count for `21 / total <= 0.35` is 60. That means 24 new non-dominant rows
would be an edge pass. M2028 instead targets:

```text
T2 target total: 72
T2 new rows: 36
T2 projected max share: 21/72 = 0.2917
```

For T3, two new non-dominant rows could pass, but that would be a fragile gate
repair. M2028 instead targets:

```text
T3 target total: 42
T3 new rows: 18
T3 projected max share: 9/42 = 0.2143
```

## T2 Source Generation Semantics

T2 must preserve:

```text
same-current observation;
same previous physical command and actuator state;
matched recent command-response window for the selected K;
different older history;
future capability difference after the aligned current state.
```

The generated rows are source candidates for future validation, not actor
inputs. They may describe hidden-dynamics or diagnostic provenance for mining
and audit, but deployable actors must never receive hidden parameters, labels,
TTC, feasibility, controller mode, reference trajectory, path error, heading
error, slip, tire force, or precomputed answers.

### T2 Quotas

Generate 36 T2 source rows:

```text
same_current_brake_authority_older_history_proxy: 6
same_current_yaw_authority_older_history_proxy: 6
same_current_steer_lag_older_history_proxy: 6
same_current_drive_brake_asymmetry_older_history_proxy: 6
same_current_rear_lateral_authority_older_history_proxy: 6
same_current_mixed_authority_older_history_proxy: 6
```

Each T2 source kind should cover:

```text
recent window K:
  0.25s
  0.5s
  1.0s

older diagnostic offsets:
  1.5s
  2.0s
  3.0s

alignment modes:
  matched_current_ego_response
  matched_previous_command
  matched_recent_window
```

The implementation may encode these as deterministic specs. It must not run
the environment in M2029.

## T3 Source Generation Semantics

T3 must preserve:

```text
deployable low-amplitude diagnostic warmup;
obstacle reveal after warmup;
no oracle actor input;
source role remains active diagnostic warmup, not a relabeled T4/T5 row.
```

Warmup modes come from the paper-route plan:

```text
brake_tap
steer_pulse
brake_plus_steer
throttle_plus_brake
lift_off_plus_steer
micro_countersteer
natural_policy
```

### T3 Quotas

Generate 18 T3 source rows:

```text
warmup_brake_authority_proxy: 3
warmup_yaw_authority_proxy: 3
warmup_steer_lag_proxy: 3
warmup_rear_lateral_authority_proxy: 3
warmup_mixed_authority_proxy: 3
warmup_terminal_boundary_recovery_proxy: 3
```

Each row should specify:

```text
warmup mode;
warmup duration;
obstacle reveal delay;
source surface variant;
role semantics;
claim boundary flags.
```

M2029 can later materialize these as no-rollout source rows and run only a
coverage projection.

## M2029 Output Contract

M2029 should implement a no-rollout source-generation preflight. It should
read M2026 repaired panel sources and write:

```text
runs/m2029_paper_route_t2_t3_source_generation_preflight/summary.json
runs/m2029_paper_route_t2_t3_source_generation_preflight/generated_source_specs.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/generated_panel_sources.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/merged_panel_sources.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/source_coverage_projection.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/generation_actions.csv
runs/m2029_paper_route_t2_t3_source_generation_preflight/claim_boundary.csv
```

The preflight should pass only if:

```text
generated T2 rows == 36
generated T3 rows == 18
all generated rows have clean claim-boundary flags
no generated row enters hidden labels or oracle values into actor input
T1/T2/T3/T4/T5 projected source coverage passes count and source-kind share
guardrail_violation_count == 0
```

Expected decision classes:

```text
t2_t3_source_generation_preflight_pass:
  projected panel coverage passes for all five families.

t2_t3_source_generation_preflight_partial:
  clean rows are generated but at least one family remains unready.

t2_t3_source_generation_preflight_fail_closed:
  generation would require relabeling, threshold weakening, or actor-contract
  violation.
```

Any partial or fail-closed result must route to audit, not execution.

## Claim Boundary

M2028 is a design milestone only. It supports:

```text
T2/T3 source-generation route is defined.
Generation quotas and semantics are explicit.
M2029 no-rollout artifact contract is specified.
```

It does not support:

```text
routing-smoke readiness;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
level3 self-identification.
```
