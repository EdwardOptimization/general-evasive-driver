# M1928 Executable V2 Task-Quality Scenario Redesign Materialization Preflight Implementation

- status: completed
- decision: `task_quality_scenario_materialization_preflight_pass_route_to_result_audit`
- result class: `task_quality_scenario_materialization_preflight_pass`
- source: `src/autodrift/executable_v2_task_quality_scenario_redesign_materialization_preflight.py`
- tests: `tests/test_executable_v2_task_quality_scenario_redesign_materialization_preflight.py`
- focused tests: `2 passed`
- summary: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/summary.json`
- executable specs: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json`
- executable specs CSV: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.csv`
- workload matrix: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_workload_matrix.csv`
- selected accepted cells: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/selected_accepted_cells.csv`
- reset/rollout/measured execution in M1928: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_task_quality_scenario_redesign_materialization_preflight.py
```

Materialization preflight:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_scenario_redesign_materialization_preflight \
  --subset-config configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json \
  --template configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json \
  --accepted-cells runs/m1923_executable_v2_task_quality_scenario_redesign_source_mining_execution/support_first_accepted_cells.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight \
  --next-blocker m1929-executable-v2-task-quality-scenario-redesign-materialization-result-audit
```

Return code:

```text
0
```

## Result

M1928 implements the focused no-rollout materializer required by M1927. It joins
the M1926 source subset, M1921 template metadata, and M1923 accepted cells to
produce executable task specs and a 12-profile workload matrix.

```text
selected_source_count: 80
executable_spec_count: 80
selected_accepted_cell_count: 80
workload_cell_count: 960
profile_count: 12
expected_profile_count: 12
unmappable_source_count: 0
missing_profile_artifact_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
passes_public_smoke_gates: true
```

Tier, role, split, and surface counts remain balanced:

```text
tier counts: 16 per tier
role counts: 20 per role
surface counts: steady_surface=40 post_friction_step=40
split counts: public_gate=67 public_debug=13
```

Representative accepted-cell rules:

```text
positive_support_max_threshold: 32
boundary_min_threshold: 32
mitigation_closest_largest_obstacle: 16
```

## Contract

Every executable spec passes the human-view env contract checks:

```text
history_length_is_one: true
action_history_mode_full: true
include_privileged_params_false: true
wheel_observation_mode_none: true
obstacle_relative_velocity_mode_zero: true
```

The executable specs include tier, label, and source-role metadata only as
artifact/evaluation metadata. They are not actor inputs.

## Interpretation Boundary

Supported:

- the redesigned 80-source panel can be turned into executable no-rollout specs;
- every selected source has a representative accepted cell;
- the workload matrix crosses all 80 specs with the 12 public profile family;
- human-view contract checks pass with no forbidden-key hits.

Unsupported:

- reset success;
- rollout success;
- measured controller performance;
- controller-family ranking;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1929-executable-v2-task-quality-scenario-redesign-branch-synthesis
```

The workflow synthesis cadence has fired. M1929 should synthesize the full
M1919-M1928 branch before any further result audit or reset/materialized
execution design. It should decide whether to promote to a new execution branch,
repair the materializer, or stop/pivot.
