# M2277 Paper-Route Current-Sim Scenario Task-Family Config Materialization

- status: completed
- result class: `current_sim_scenario_task_family_config_materialization_pass`
- manifest: `experiments/manifests/m2277-paper-route-current-sim-scenario-task-family-config-materialization.json`
- implementation: `src/autodrift/paper_route_current_sim_scenario_task_family_config_materialization.py`
- tests: `tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py`
- config artifact: `configs/paper_route_current_sim_scenario_task_family_v0.json`
- run artifact: `runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/summary.json`
- reset/rollout/measured execution in M2277: `false`
- policy actions executed in M2277: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_config_materialization \
  --config-output configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization \
  --next-blocker m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit
```

## Result

```text
result_class: current_sim_scenario_task_family_config_materialization_pass
scenario_family_count: 6
scenario_spec_count: 72
min_specs_per_role: 12
metadata_missing_required_field_count: 0
duplicate_scenario_spec_id_count: 0
labels_enter_actor_input_count: 0
actor_contract_violation_count: 0
ranking_admissible_count: 0
guardrail_violation_count: 0
passes_public_materialization_gates: true
```

Role-family counts:

```text
R0_stable_avoidable: 12
R1_aeb_infeasible_stable_aes: 12
R2_handling_limit_drift_capable_avoidance: 12
R3_recovery_after_limit: 12
R4_unavoidable_mitigation: 12
R5_hidden_dynamics_robustness: 12
```

Timing and lateral metadata support:

```text
obstacle_timing_bucket_counts:
  early_far: 24
  mid: 24
  late_close: 24

obstacle_lateral_offset_bucket_counts:
  centerline: 34
  left_offset: 19
  right_offset: 19

hidden_dynamics_bucket_counts:
  high_mass_or_inertia: 4
  low_mu: 15
  nominal: 15
  slow_steer_actuator: 19
  tire_stiffness_shift: 8
  weak_brake: 11
```

## Corrected Role Mapping

M2277 uses the M2276-corrected mapping:

```text
aeb_feasible -> R0_stable_avoidable
aes_feasible -> R1_aeb_infeasible_stable_aes
drift_required -> R2/R3 handling-limit or recovery roles
unavoidable -> R4_unavoidable_mitigation
same-scene hidden-dynamics bundles -> R5_hidden_dynamics_robustness
```

These labels remain metadata only:

```text
labels_enter_actor_input_count: 0
actor_contract_id: P0_human_view_no_wheel_no_oracle
obstacle_relative_velocity_mode: zero
wheel_observation_mode: none
include_privileged_params: false
history_length: 1
```

## Unsupported Capability Boundary

M2277 intentionally does not silently approximate unsupported simulator
capability:

```text
unsupported_capability_count: 44
unsupported_execution_blocker_count: 38
silent_unsupported_approximation_count: 0
execution_admissible_without_instrumentation: false
primary_route: scenario_task_family_result_audit_route_to_instrumentation_repair
```

The `38` execution blockers are left/right emergency obstacle lateral-offset
rows. Current emergency obstacle placement is centerline-only, so these rows are
materialized as desired scenario specs but blocked from reset/rollout until the
simulator adds explicit obstacle lateral-offset instrumentation.

The remaining unsupported rows are future capability records, not current
execution blockers:

```text
single_wheel_blowout_or_puncture
wheel_specific_grip_loss
half_shaft_or_single_side_drive_torque_loss
brake_side_imbalance
steering_deadzone_or_partial_actuator_fault
sensor_dropout_or_bias
```

These are recorded for future higher-fidelity or explicit model-extension work.
They are not current-sim claims.

## Artifacts

```text
configs/paper_route_current_sim_scenario_task_family_v0.json
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/summary.json
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/scenario_family_specs.json
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/scenario_family_specs.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/materialized_config_matrix.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/metadata_schema.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/role_family_support_targets.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/unsupported_capability_rows.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/contract_violations.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/missing_required_fields.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/duplicate_scenario_spec_ids.csv
runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization/claim_boundary.csv
```

## Verification

Commands run:

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_config_materialization.py

python -m compileall -q src tests

PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_config_materialization \
  --config-output configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2277_paper_route_current_sim_scenario_task_family_config_materialization \
  --next-blocker m2278-paper-route-current-sim-scenario-task-family-config-materialization-result-audit
```

Focused test result:

```text
3 passed
```

## Claim Boundary

Supported:

```text
M2277 materialized a no-reset role-supported scenario task-family config pack.
The pack preserves the actor contract and corrected role mapping.
Unsupported current-sim capability is explicitly reported.
```

Unsupported:

```text
execution admissible without lateral-offset instrumentation
reset or rollout result
training result
controller-family ranking
winner selection
finite-window-vs-GRU conclusion
paper-level evidence
level3 self-identification
```

## Decision

Route to M2278 result audit. The likely route after audit is obstacle
lateral-offset instrumentation repair before any reset, rollout, measured
execution, training, or ranking.
