# M1997 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Reset Validation Rerun Result Audit

- status: completed
- decision: `task_quality_calibrated_outcome_support_reset_rerun_audit_route_to_measured_runner_quota_parameterization_design`
- audited summary: `runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/summary.json`
- reset rerun in M1997: `false`
- rollout/measured execution in M1997: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M1996 is a clean repaired reset-validation pass:

```text
result_class: task_quality_calibrated_reset_validation_preflight_pass
reset_attempt_count: 80
reset_success_count: 80
reset_failure_count: 0
observation_finite_count: 80
observation_dimension_failure_count: 0
obstacle_initialized_count: 80
expected_quota_source: executable_task_specs
quota_metadata_missing_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
contract_violation_count: 0
label_actor_input_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
environment_reset_started: true
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

This restores reset-validation pass evidence for the M1986 repaired
outcome-support panel.

## Measured Runner Readiness Check

M1997 does not admit measured execution directly. The calibrated measured
runner has the same class of historical hard-coded quota constants that caused
M1990 to fail before M1993 repaired the reset validator.

Current M1986 workload source-kind counts:

```text
anchor_neighborhood: 288
mitigation_isolation_check: 240
offtrack_boundary_relief: 192
success_stabilizer: 240
```

Legacy calibrated measured-runner expected source-kind counts:

```text
anchor_neighborhood: 384
mitigation_isolation_check: 192
offtrack_boundary_relief: 96
success_stabilizer: 288
```

Therefore a direct measured execution would likely repeat the same stale-quota
metric artifact at the rollout layer. The correct next step is to design the
measured-runner equivalent of M1993 before command-designing the measured
execution rerun.

## Supported Claims

M1997 supports:

- the repaired outcome-support 80-spec panel is reset-valid;
- the reset validator quota repair worked for the M1986 panel;
- measured execution command design is technically closer, but still blocked
  by measured-runner quota-gate readiness;
- the stale-quota issue should be fixed at the measured-runner layer before
  burning a 960-row rollout.

M1997 does not support:

- measured rollout success;
- controller-family ranking;
- finite-window vs GRU comparison;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification.

## Next Route

Decision:

```text
route_to_measured_runner_quota_parameterization_design
```

M1998 should design an artifact-driven quota repair for
`src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py`,
analogous to M1992/M1993, before measured execution command design.

M1998 must not run measured execution.
