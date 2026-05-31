# M1935 Executable V2 Task-Quality Measured Execution Design

- status: completed
- decision: `task_quality_measured_execution_design_requires_focused_runner_adapter`
- branch: `paper_route_task_quality_reset_execution`
- reset gate: `runs/m1933_executable_v2_task_quality_reset_validation_preflight/summary.json`
- executable specs: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json`
- workload matrix: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_workload_matrix.csv`
- target workload cells: `960`
- target specs: `80`
- target profiles: `12`
- rollout/measured execution in M1935: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Decision

M1935 does not admit direct measured rollout. It admits a focused measured
runner adapter implementation first.

Reason:

```text
M1928 workload rows are not schema-compatible with the existing measured
runners without metadata loss or legacy-field assumptions.
```

The measured execution target remains:

```text
80 reset-valid executable specs x 12 controller profiles = 960 public
diagnostic rollout cells
```

but M1936 must implement the adapter/wrapper before any real rollout.

## Compatibility Audit

### Generic Full Rollout Runner

File:

```text
src/autodrift/controller_family_full_rollout_execution.py
```

Reusable pieces:

- `load_executable_specs` can read an `executable_task_specs` payload;
- `env_config_for_executable_profile` can rebuild scenario config while
  preserving profile-specific history length and human-view contract;
- `_load_profile_cache` can load controller profiles and checkpoints;
- `run_episode_with_policy` path is the right execution primitive;
- resumability and failure-row preservation are useful patterns.

Not exact for M1928:

- `run_workload_cell` writes legacy fields that M1928 workload rows do not have:
  `task_family`, `source_edge`, `window_tag`, `executable_source_family`, and
  `env_template_family`;
- aggregate/comparison outputs are old controller-family diagnostics, not
  task-quality tier/role/surface diagnostics;
- failure rows do not preserve M1928 `feasibility_tier_id`,
  `source_role_semantics`, `source_split`, `surface_variant`,
  `target_boundary_mode`, or `selected_accepted_cell_rule`;
- direct execution would either fail on missing keys or silently encourage an
  ad hoc compatibility shim.

Conclusion:

```text
do not run the generic runner directly over M1928.
```

### Support-First Measured Runner

Files:

```text
src/autodrift/executable_v2_support_first_measured_runner_adapter.py
src/autodrift/executable_v2_support_first_measured_runner_execution.py
```

Not exact for M1928:

- expects `support_first_measured_executable_specs`;
- expects support-first role/surface IDs and scenario profile fields;
- carries old support-first metadata, not the M1928 five-tier task-quality
  scenario redesign schema.

Conclusion:

```text
do not route M1928 through support-first measured runner schemas.
```

### Repair-Axis Runner

File:

```text
src/autodrift/executable_v2_support_first_task_quality_repair_axis_execution.py
```

Not exact for M1928:

- expects repair-axis matrix rows;
- supports import/postprocess semantics from older measured panels;
- is designed for geometry/semantics repair variants, not a fresh reset-valid
  source distribution.

Conclusion:

```text
do not route M1928 through repair-axis execution schemas.
```

## M1936 Adapter Requirements

M1936 should implement a focused adapter/wrapper, tentatively:

```text
src/autodrift/executable_v2_task_quality_measured_runner.py
tests/test_executable_v2_task_quality_measured_runner.py
```

M1936 must not run the real 960-cell workload. It should use mocked/focused
tests and synthetic rows.

The adapter should:

- load M1928 `executable_task_specs`;
- load M1928 `executable_workload_matrix`;
- join workload rows to specs by `task_source_id`;
- validate `80` specs, `960` workload rows, and `12` controller profiles;
- preserve source/tier/role/split/surface metadata in every episode and failure
  row;
- preserve `target_boundary_mode` and `selected_accepted_cell_rule`;
- preserve `profile_config_path` and `checkpoint_path` from workload rows;
- load profile configs/checkpoints through an injectable runtime path;
- execute one rollout per workload row only when an explicit measured execution
  command later enables it;
- write complete episode/failure rows and aggregate rows by profile, tier, role,
  surface, sampled label, outcome, and termination reason;
- write claim-boundary rows that keep ranking and paper claims blocked.

It should reuse the generic runner's execution primitives where appropriate,
but not reuse its legacy output schema.

## Later Execution Contract

After M1936 implementation and tests, the staged route should be:

```text
M1936: adapter implementation, mocked/focused tests only
M1937: exact measured execution command design
M1938: real 960-cell public diagnostic measured execution
M1939: result audit and outcome localization decision
```

The eventual measured execution pass gate should require:

```text
episode_count == 960
failure_count == 0
profile_count == 12
spec_count == 80
tier_count == 5
role_count == 4
surface_count == 2
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

M1935 supports only:

```text
measured rollout requires a focused M1928 task-quality runner adapter before
execution.
```

It does not support:

- rollout success;
- controller ranking;
- policy improvement;
- finite-window vs GRU comparison;
- paper-level benchmark evidence;
- level3 self-ID.

## Next

Next milestone:

```text
m1936-executable-v2-task-quality-measured-runner-adapter-implementation
```

M1936 should implement the focused adapter and tests without running the real
960-cell measured workload.
