# M1932 Executable V2 Task-Quality Reset Validation Command Design

- status: completed
- decision: `task_quality_reset_validation_command_design_admit_execution`
- branch: `paper_route_task_quality_reset_execution`
- source helper: `src/autodrift/executable_v2_task_quality_reset_validation_preflight.py`
- input specs: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json`
- output dir: `runs/m1933_executable_v2_task_quality_reset_validation_preflight`
- target spec count: `80`
- expected observation dim: `72`
- real reset execution in M1932: `false`
- rollout/measured execution in M1932: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1933 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_reset_validation_preflight \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1933_executable_v2_task_quality_reset_validation_preflight \
  --eval-seed-base 193300 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1934-executable-v2-task-quality-reset-validation-result-audit
```

M1932 does not run this command. It freezes it for M1933.

## Expected Artifacts

M1933 must write:

```text
runs/m1933_executable_v2_task_quality_reset_validation_preflight/summary.json
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_rows.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_failure_rows.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/contract_rows.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_distribution_by_tier.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_distribution_by_role.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/reset_distribution_by_surface.csv
runs/m1933_executable_v2_task_quality_reset_validation_preflight/claim_boundary.csv
```

## Pass Gates

M1933 passes only if:

```text
result_class == task_quality_reset_validation_preflight_pass
input_executable_spec_count == 80
target_executable_spec_count == 80
reset_attempt_count == 80
reset_success_count == 80
reset_failure_count == 0
observation_finite_count == 80
observation_dimension_failure_count == 0
obstacle_initialized_count == 80
contract_violation_count == 0
label_actor_input_violation_count == 0
private_holdout_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
environment_reset_started == true
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If any row fails reset or contract checks, M1933 must fail closed and route to a
result/failure audit. It must not repair and rerun inside the same milestone.

## Failure Taxonomy

M1933 should classify failures as:

```text
schema_incompatible
env_config_rebuild_failure
human_view_contract_violation
reset_sampling_failure
observation_contract_failure
metadata_join_failure
guardrail_violation
```

Any `reset_sampling_failure` is scenario evidence, not a reason to tune
controller profiles. Controller-family ranking remains blocked until reset
passes and measured rollout is designed separately.

## Claim Boundary

If M1933 passes, it may claim only:

```text
the M1928 80-spec public task-quality scenario panel is reset-valid under the
current simulator and strict human-view observation contract.
```

It still cannot claim:

- rollout success;
- controller-family ranking;
- policy improvement;
- finite-window vs GRU comparison;
- level3 self-identification;
- paper-level benchmark evidence.

## Next

Next milestone:

```text
m1933-executable-v2-task-quality-reset-validation-preflight
```

M1933 may run the frozen reset-only command. Interpretation must be deferred to
M1934 result audit.
