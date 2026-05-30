# M1823 Executable V2 Stable Source Targeted Reset Sampler Repair Implementation

- status: completed
- decision: `stable_source_targeted_reset_sampler_repair_implementation_pass_route_to_execution_design`
- module: `src/autodrift/executable_v2_stable_source_targeted_reset_sampler_repair.py`
- test: `tests/test_executable_v2_stable_source_targeted_reset_sampler_repair.py`
- project artifact repair run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Summary

M1823 implements the no-reset source-level sampler repair planner designed in
M1822. The planner reads a targeted reset payload plus reset diagnostic rows,
groups failures by materialized source, classifies each source as systematic or
sparse, and emits a repaired executable v2 payload candidate for later reset
validation.

The implementation uses offline `classify_obstacle_scenario` label-density
checks to select repaired obstacle sampler ranges. It does not instantiate
`AutoDriftEnv` and does not call `env.reset`.

## Implemented Artifacts

The planner writes:

```text
summary.json
source_sampler_repair_targets.csv
source_sampler_repair_specs.json
source_sampler_repair_specs.csv
source_sampler_repair_matrix.csv
repaired_targeted_reset_executable_v2_panel_specs.json
source_sampler_repair_claim_boundary.csv
```

The repaired payload uses:

```text
executable_v2_panel_specs
```

and is meant for a later targeted reset-only preflight.

## Repair Classes

Systematic source failures:

```text
source_sampler_repair_class=systematic
max_sample_attempts>=10000
```

Sparse source failures:

```text
source_sampler_repair_class=sparse
max_sample_attempts>=5000
```

For `aes_feasible`, the planner preserves:

```text
allowed_labels=["aes_feasible"]
require_aeb_infeasible=true
```

For `aeb_feasible`, the planner preserves:

```text
allowed_labels=["aeb_feasible"]
require_aeb_infeasible=false
```

## Verification

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest tests/test_executable_v2_stable_source_targeted_reset_sampler_repair.py -q
```

Result:

```text
2 passed in 0.17s
```

The tests verify:

- systematic AES and sparse AEB source classification;
- source-level repaired payload generation;
- profile-control preservation;
- label metadata stays out of actor input;
- ranking remains blocked by default;
- fully successful sources pass through without repair;
- no environment reset, rollout, policy action, training, replay, PPO,
  promotion, ranking, paper-level, or level3 claim.

## Expected Project Execution Counts

A later no-reset execution should target:

| field | expected |
| --- | ---: |
| `repair_target_source_count` | 3 |
| `systematic_source_count` | 2 |
| `sparse_source_count` | 1 |
| `profile_control_count` | 12 |
| `repaired_executable_spec_count` | 36 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `guardrail_violation_count` | 0 |

## Guardrails

- project artifact repair run: `false`
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

- no-reset repair planner implementation;
- focused tests pass;
- repaired payload candidate schema exists.

Unsupported:

- project artifact repair result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to:

```text
m1824-executable-v2-stable-source-targeted-reset-sampler-repair-execution-design
```

M1824 should pre-register the exact no-reset planner command over M1816/M1820
artifacts. It should not execute project repair or environment reset.
