# M1822 Executable V2 Stable Source Targeted Reset Sampler Repair Design

- status: completed
- decision: `stable_source_targeted_reset_sampler_repair_design_admit_no_reset_planner`
- branch: `paper_route_executable_v2_targeted_reset_validation`
- source audit: `docs/m1821-executable-v2-stable-source-targeted-reset-feasibility-result-audit.md`
- reset run: `false`
- rollout/training/replay/PPO: `false`

## Problem

M1820 proved that the converted payload shape is not enough. The current
materialized sources still fail reset sampling:

```text
attempted_spec_count=36
reset_success_count=10
sampling_failure_count=26
```

M1821 localized this as:

```text
systematic_aes_sampler_infeasibility: 24 rows
sparse_aeb_seed_sampling_failure: 2 rows
```

The two `aes_feasible` sources fail for every profile seed. The `aeb_feasible`
source succeeds on 10 of 12 profile seeds and fails on 2.

## Design Principle

Repair must be source-level, not profile-specific.

The repair may change materialized source sampler metadata and obstacle
sampling ranges. It must not:

- change actor inputs;
- tune individual profile behavior;
- change reward, dynamics, or termination;
- admit measured execution or ranking before reset support;
- hide labels in actor observations.

## Root-Cause Model

`env_config_for_executable_profile` preserves `executable_spec["env_config"]`
and only applies profile-level history length plus observation-contract fields.
Therefore the dominant failure is not a profile merge overwriting obstacle
config.

The likely failure is sampler support:

- M1811 patched `allowed_labels`, `require_aeb_infeasible`, and
  `max_sample_attempts`;
- M1811 did not reconstruct the `distance_range`, `half_width_range`, timing
  filters, or other sampler ranges to make the target label probable;
- for `aes_feasible`, the old source ranges appear to contain no accepted
  scenarios under the current speed/mu distribution;
- for `aeb_feasible`, the source has support but is seed-fragile.

## Repair Targets

Systematic AES repair targets:

```text
m1811-stable-bp-000: target label aes_feasible, hidden bucket nominal
m1811-stable-bp-001: target label aes_feasible, hidden bucket friction_step
```

Sparse AEB repair target:

```text
m1811-stable-bp-002: target label aeb_feasible, hidden bucket brake_variation
```

## M1823 No-Reset Planner

M1823 should implement a no-reset sampler repair planner. It should read:

```text
runs/m1816_executable_v2_stable_source_reset_validation_adapter/targeted_reset_executable_v2_panel_specs.json
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/reset_stress_rows.csv
runs/m1820_executable_v2_stable_source_targeted_reset_feasibility_preflight/sampling_failure_rows.csv
```

and write repaired candidate artifacts without calling `env.reset`:

```text
summary.json
source_sampler_repair_targets.csv
source_sampler_repair_specs.json
source_sampler_repair_specs.csv
source_sampler_repair_matrix.csv
source_sampler_repair_claim_boundary.csv
```

The planner should:

1. group failures by materialized source and requested label;
2. classify sources as systematic or sparse;
3. use offline `classify_obstacle_scenario` density checks, not environment
   reset, to propose source-level obstacle range patches;
4. preserve all 12 profile controls for each source;
5. emit a repaired executable v2 payload candidate for a later reset preflight.

## Repair Policy

For systematic `aes_feasible` sources:

- keep `allowed_labels=["aes_feasible"]`;
- keep `require_aeb_infeasible=true`;
- raise `max_sample_attempts` only as a secondary measure;
- reconstruct or widen `distance_range` and `half_width_range` using offline
  label-density checks so `aes_feasible` has observable support;
- preserve target hidden/road/timing/lateral buckets as metadata, but do not
  force impossible sampler windows.

For sparse `aeb_feasible` source:

- keep `allowed_labels=["aeb_feasible"]`;
- keep `require_aeb_infeasible=false`;
- increase seed robustness by increasing sample attempts and, if needed,
  modestly widening the source-level range;
- do not create per-profile special cases.

## Expected Planner Counts

M1823 should target:

| field | expected |
| --- | ---: |
| `repair_target_source_count` | 3 |
| `systematic_source_count` | 2 |
| `sparse_source_count` | 1 |
| `profile_control_count` | 12 |
| `repaired_executable_spec_count` | 36 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `environment_reset_started` | 0 |
| `guardrail_violation_count` | 0 |

## Later Reset Criteria

A later reset run should require:

```text
attempted_spec_count=36
reset_success_count=36
sampling_failure_count=0
profile_count=12
role_surface_count=1
labels_enter_actor_input_count=0
ranking_admissible_by_default_count=0
guardrail_violation_count=0
```

If the repaired payload still fails, the result should be audited before any
further repair.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- source-level sampler repair design;
- systematic and sparse reset failures require separate handling;
- no-reset planner implementation is admitted.

Unsupported:

- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to:

```text
m1823-executable-v2-stable-source-targeted-reset-sampler-repair-implementation
```

M1823 should implement the no-reset planner with focused tests. It should not
execute project artifact repair or environment reset.
