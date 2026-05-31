# M1956 Executable V2 Task-Quality Calibrated Source Materialization Selector Implementation

- status: completed
- decision: `task_quality_calibrated_materialization_selector_pass_route_to_preflight_command_design`
- branch: `paper_route_task_quality_calibrated_materialization`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_source_materialization_selector.py`
- focused tests: `3 passed`
- config: `configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json`
- summary: `runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/summary.json`
- reset/rollout/measured execution in M1956: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M1956 implements the deterministic source-only selector designed in M1955 and
runs it against the real M1952 calibrated source-mining artifacts:

```text
input source rows: 160
eligible sources: 130
input accepted cells: 5981
selected sources: 80
expected controller profiles: 12
expected planned workload cells: 960
guardrail violation count: 0
result_class: task_quality_calibrated_materialization_selector_pass
```

Selected source-kind quotas:

```text
anchor_neighborhood: 32 / 32
success_stabilizer: 24 / 24
offtrack_boundary_relief: 8 / 8
mitigation_isolation_check: 16 / 16
```

Calibrated-anchor provenance:

```text
calibrated_anchor_selected_count: 32
post_friction_step: 16
steady_surface: 16
```

Success-stabilizer preservation:

```text
success_stabilizer_selected_count: 24
post_friction_step: 12
steady_surface: 12
```

Other checks:

```text
selected_supported_source_count: 80
duplicate_candidate_source_id_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
profile_specific_tuning_count: 0
selected_accepted_cell_count_total: 3382
```

## Artifacts

M1956 writes:

```text
configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/summary.json
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/selected_sources.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/selection_failures.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/source_kind_quota_summary.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/role_surface_quota_summary.csv
runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/claim_boundary.csv
```

## Interpretation Boundary

Supported by M1956:

- the M1952 calibrated source pool can produce a bounded 80-source
  materialization subset;
- source-kind quotas, role/surface quotas, and calibrated-anchor provenance
  pass exactly;
- a 960-cell planned workload target is now available for the next
  materialization/preflight stage.

Unsupported by M1956:

- environment reset validity;
- executable spec correctness;
- measured rollout success;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design
```

M1957 should design the exact preflight/materialization command path for the
M1956 subset before any reset, rollout, measured execution, ranking, paper
claim, or level3 self-ID claim.
