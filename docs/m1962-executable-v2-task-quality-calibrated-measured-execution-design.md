# M1962 Executable V2 Task-Quality Calibrated Measured Execution Design

- status: completed
- decision: `task_quality_calibrated_measured_execution_design_requires_focused_runner`
- branch: `paper_route_task_quality_calibrated_materialization`
- reset audit: `docs/m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit.md`
- executable specs: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json`
- planned workload: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv`
- target workload cells: `960`
- target specs: `80`
- target profiles: `12`
- rollout/measured execution in M1962: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Decision

M1962 does not admit direct measured execution with the old M1936 runner. It
admits a focused calibrated measured-runner implementation first.

Reason:

```text
The existing task-quality measured runner can reuse rollout primitives, but its
output schema is still centered on old fields such as feasibility_tier_id and
surface_variant. The M1958 calibrated panel uses repair_source_kind,
selection_quota_name, parent_feasibility_tier_id, parent_surface_variant, and
normalized_surface_variant. Direct execution would either drop those fields or
produce weak aggregates that are not useful for the calibrated repair branch.
```

The measured execution target remains:

```text
80 reset-valid executable specs x 12 controller profiles = 960 public
diagnostic rollout cells
```

but M1963 must implement the calibrated adapter/wrapper before real rollout.

## Compatibility Audit

### Existing Task-Quality Measured Runner

File:

```text
src/autodrift/executable_v2_task_quality_measured_runner.py
```

Reusable pieces:

- `load_executable_task_specs`;
- `load_workload_rows`;
- profile loading and checkpoint runtime helpers;
- `env_config_for_executable_profile`;
- `run_episode_with_policy`;
- resumability and failure-row preservation.

Not exact for M1958:

- passthrough metadata is hard-coded around `feasibility_tier_id`,
  `surface_variant`, and `selected_accepted_cell_rule`;
- calibrated fields such as `repair_source_kind`, `selection_quota_name`,
  `parent_feasibility_tier_id`, `parent_surface_variant`,
  `normalized_surface_variant`, `base_geometry_source`, and
  `representative_cell_rule` are not first-class episode fields;
- aggregate outputs do not include repair-source-kind or role/surface calibrated
  aggregates;
- pass gates do not require calibrated metadata preservation;
- direct use would undercut the purpose of M1955-M1961, which was to preserve
  calibrated repair provenance before measured execution.

Conclusion:

```text
do not run the existing task-quality measured runner directly over M1958.
```

### Generic Full Rollout Runner

File:

```text
src/autodrift/controller_family_full_rollout_execution.py
```

Useful as an execution primitive, but not as the direct result schema. It does
not know the calibrated task-quality panel metadata and would produce legacy
controller-family diagnostics.

Conclusion:

```text
reuse primitives only; do not use direct generic outputs.
```

## M1963 Adapter Requirements

M1963 should implement:

```text
src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py
tests/test_executable_v2_task_quality_calibrated_measured_runner.py
```

M1963 must not run the real 960-cell measured workload. It should use focused
mocked tests and synthetic calibrated rows.

The adapter should:

- load M1958 `executable_task_specs`;
- load M1958 `planned_workload.csv`;
- join workload rows to specs by `task_source_id`;
- validate `80` specs, `960` workload rows, and `12` controller profiles;
- preserve calibrated source metadata in every episode and failure row;
- preserve profile config/checkpoint provenance;
- write complete episode/failure rows and aggregates by:
  - profile;
  - repair source kind;
  - source role;
  - normalized surface;
  - repair source kind + source role + normalized surface;
  - sampled label;
  - outcome;
  - termination reason;
- keep `controller_family_ranking_claim_made == false` in all artifacts;
- support an injectable rollout function for tests;
- use real rollout primitives only when a later frozen execution command
  enables it.

## Later Execution Contract

After M1963 implementation and tests, the staged route should be:

```text
M1963: calibrated measured-runner implementation, mocked/focused tests only
M1964: exact measured execution command design
M1965: real 960-cell public diagnostic measured execution
M1966: result audit and outcome/localization decision
```

The eventual measured execution pass gate should require:

```text
episode_count == 960
failure_count == 0
profile_count == 12
spec_count == 80
source_kind_quota_pass == true
role_surface_quota_pass == true
metric_completeness_failure_count == 0
guardrail_violation_count == 0
environment_rollout_started == true
policy_action_executed == true
measured_rollout_started == true
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Claim Boundary

M1962 supports only:

```text
measured rollout requires a focused calibrated runner adapter before execution.
```

It does not support:

- rollout success;
- controller ranking;
- policy improvement;
- finite-window vs GRU comparison;
- paper-level benchmark evidence;
- level3 self-identification.

## Next

Next milestone:

```text
m1963-executable-v2-task-quality-calibrated-measured-runner-implementation
```

M1963 should implement the focused calibrated measured runner and tests without
running the real 960-cell measured workload.
