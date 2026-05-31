# M1961 Executable V2 Task-Quality Calibrated Reset Validation Result Audit

- status: completed
- decision: `task_quality_calibrated_reset_validation_audit_admit_measured_execution_design`
- branch: `paper_route_task_quality_calibrated_materialization`
- audited summary: `runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/summary.json`
- reset/rollout/measured execution in M1961: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audited Result

M1960 is a clean reset-validation pass:

```text
result_class: task_quality_calibrated_reset_validation_preflight_pass
input_executable_spec_count: 80
target_executable_spec_count: 80
reset_attempt_count: 80
reset_success_count: 80
reset_failure_count: 0
observation_finite_count: 80
observation_dimension_failure_count: 0
obstacle_initialized_count: 80
contract_violation_count: 0
label_actor_input_violation_count: 0
forbidden_key_violation_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
guardrail_violation_count: 0
```

The calibrated repair-source distribution is preserved:

```text
anchor_neighborhood: 32
success_stabilizer: 24
offtrack_boundary_relief: 8
mitigation_isolation_check: 16
```

The sampled labels remain role-consistent:

```text
aeb_feasible: 44
aes_feasible: 14
drift_required: 9
unavoidable: 13
```

## Supported Claims

M1961 supports only:

- the M1958 calibrated 80-spec diagnostic panel is reset-valid in the current
  simulator;
- strict human-view observation contract checks pass at reset;
- calibrated repair metadata survives materialization and reset validation;
- the branch may proceed to measured execution design.

## Unsupported Claims

M1961 does not support:

- rollout success;
- measured controller performance;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- finite-window vs GRU comparison;
- level3 self-identification evidence.

## Route Decision

M1961 admits a measured execution design milestone, not direct measured
execution. M1962 must decide the exact runner/protocol for:

```text
input specs: runs/m1960-compatible M1958 executable_task_specs.json
planned workload: runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
target cells: 960
controller profiles: 12
source metadata preservation: required
ranking: blocked until post-execution audit
```

The measured execution route must preserve:

```text
repair_source_kind
selection_quota_name
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
base_geometry_source
representative_cell_rule
sampled obstacle geometry
profile_name
checkpoint/config provenance
```

## Next

Next milestone:

```text
m1962-executable-v2-task-quality-calibrated-measured-execution-design
```

M1962 should design the measured execution protocol. It must not run measured
execution inside the design milestone.
