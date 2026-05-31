# M1971 Executable V2 Task-Quality Calibrated Repaired Reset Validation Command Design

- status: completed
- decision: `task_quality_calibrated_repaired_reset_command_design_admit_execution`
- repaired executable specs: `runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json`
- reset execution in M1971: `false`
- rollout/measured execution in M1971: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1972 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_reset_validation_preflight \
  --executable-task-specs runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json \
  --output-dir runs/m1972_executable_v2_task_quality_calibrated_reset_validation_preflight_repaired \
  --eval-seed-base 197200 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1973-executable-v2-task-quality-calibrated-repaired-reset-validation-result-audit
```

M1971 does not run this command. It freezes it for M1972.

## Pass Gates

M1972 passes only if:

```text
result_class == task_quality_calibrated_reset_validation_preflight_pass
reset_attempt_count == 80
reset_success_count == 80
reset_failure_count == 0
observation_finite_count == 80
observation_dimension_failure_count == 0
obstacle_initialized_count == 80
contract_violation_count == 0
label_actor_input_violation_count == 0
forbidden_key_violation_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
guardrail_violation_count == 0
environment_reset_started == true
environment_rollout_started == false
measured_rollout_started == false
policy_action_executed == false
training_started == false
replay_started == false
ppo_used == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If reset validation fails, M1972 must preserve reset failure artifacts and route
to result/failure audit. It must not repair and rerun inside the same milestone.

## Claim Boundary

If M1972 passes, it may claim only:

```text
the repaired calibrated 80-spec panel is reset-valid under the current
simulator and strict human-view observation contract.
```

It still cannot claim measured rollout success, controller-family ranking,
paper-level benchmark evidence, policy improvement, finite-window-vs-GRU
comparison, or level3 self-identification.

## Next

Next milestone:

```text
m1972-executable-v2-task-quality-calibrated-repaired-reset-validation-preflight
```

M1972 may run only the frozen reset-only command.
