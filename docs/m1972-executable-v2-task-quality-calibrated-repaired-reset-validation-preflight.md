# M1972 Executable V2 Task-Quality Calibrated Repaired Reset Validation Preflight

- status: completed
- decision: `task_quality_calibrated_repaired_reset_validation_pass_route_to_audit`
- run dir: `runs/m1972_executable_v2_task_quality_calibrated_reset_validation_preflight_repaired`
- environment reset in M1972: `true`
- rollout/measured execution in M1972: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1972 ran the frozen reset-only command:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_reset_validation_preflight \
  --executable-task-specs runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json \
  --output-dir runs/m1972_executable_v2_task_quality_calibrated_reset_validation_preflight_repaired \
  --eval-seed-base 197200 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1973-executable-v2-task-quality-calibrated-repaired-reset-validation-result-audit
```

## Result

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
environment_reset_started: true
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
```

Sampled labels:

```text
aeb_feasible: 44
aes_feasible: 14
drift_required: 9
unavoidable: 13
```

Source-kind counts:

```text
anchor_neighborhood: 32
success_stabilizer: 24
offtrack_boundary_relief: 8
mitigation_isolation_check: 16
```

## Interpretation Boundary

Supported by M1972:

- the repaired calibrated 80-spec panel is reset-valid under the current
  simulator and strict human-view observation contract;
- offtrack parent-tier normalization did not break reset initialization;
- no rollout, measured execution, policy action, training, replay, PPO,
  controller ranking, paper-level, or level3 self-ID claim was made.

Unsupported by M1972:

- measured rollout success;
- controller-family ranking;
- policy performance comparison;
- paper-level benchmark evidence;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Next milestone:

```text
m1973-executable-v2-task-quality-calibrated-repaired-reset-validation-result-audit
```

M1973 should audit the reset-valid repaired panel before measured execution
design is admitted.
