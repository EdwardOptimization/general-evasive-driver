# M1991 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Reset Validation Result Audit

- status: completed
- decision: `task_quality_calibrated_outcome_support_reset_validation_audit_route_to_quota_parameterization_repair_design`
- audited summary: `runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/summary.json`
- reset rerun in M1991: `false`
- rollout/measured execution in M1991: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- failure taxonomy: `metric_artifact`

## Audit Result

M1990 is a fail-closed result caused by stale quota expectations in the reset
validator. It is not a reset, contract, observation, or guardrail failure.

```text
result_class: task_quality_calibrated_reset_validation_preflight_fail
input_executable_spec_count: 80
reset_attempt_count: 80
reset_success_count: 80
reset_failure_count: 0
observation_finite_count: 80
observation_dimension_failure_count: 0
obstacle_initialized_count: 80
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
source_kind_quota_pass: false
role_surface_quota_pass: false
passes_public_smoke_gates: false
```

Observed M1990 source-kind counts:

```text
anchor_neighborhood: 24
mitigation_isolation_check: 20
offtrack_boundary_relief: 16
success_stabilizer: 20
```

These counts are consistent with the M1986 selected repair-axis quotas after
normalizing names:

```text
offtrack_anchor_relief -> anchor_neighborhood: 24
mitigation_metric_isolation -> mitigation_isolation_check: 8 diagnostic rows,
  plus collision_mitigation_relief mapped to mitigation-oriented rows: 12,
  total mitigation_isolation_check: 20
offtrack_boundary_relief_extension -> offtrack_boundary_relief: 16
success_support_expansion -> success_stabilizer: 20
```

The validator still checks the older calibrated materialization expected
distribution:

```text
anchor_neighborhood: 32
mitigation_isolation_check: 16
offtrack_boundary_relief: 8
success_stabilizer: 24
```

Therefore `result_class=fail` is a correct fail-closed outcome under the old
validator, but the old validator is no longer an exact schema match for the
M1986 repaired outcome-support panel.

## Classification

Failure type:

```text
metric_artifact
```

Rationale:

- the measured reset operation itself succeeds for all `80` specs;
- actor-input contract and guardrails are clean;
- the only failing checks are distribution gates;
- the distribution gates are hard-coded to the older M1956/M1958 panel rather
  than parameterized from the active materialization artifact.

This is not classified as:

```text
scenario_sampling_failure:
  no spec failed reset or obstacle initialization.

contract_violation:
  contract_violation_count == 0 and label_actor_input_violation_count == 0.

training_instability / proof_washout / behavior_regression:
  no policy action, rollout, training, replay, PPO, or checkpoint update ran.
```

## Supported Claims

M1991 supports:

- M1990 executed only the frozen reset-only command;
- all M1986 executable specs reset with finite 72-dimensional human-view
  observations;
- the M1986 executable panel is technically reset-capable under the current
  simulator;
- the current reset validator's quota checks are stale for M1986;
- a quota-parameterized validator repair is needed before rerun can produce a
  pass result.

M1991 does not support:

- marking M1990 as passed without rerun under a repaired gate;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU comparison;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification.

## Next Route

Decision:

```text
route_to_quota_parameterization_repair_design
```

M1992 should design a reset-validator repair that does not hard-code
source-kind and role-surface quotas for one historical panel. The repaired
validator should accept expected distribution inputs from the active
materialization artifact or an explicit expected-quota file, and it should fail
closed if the expected distribution is missing or inconsistent.

M1992 must not rerun reset. After implementation and focused tests, a later
milestone can rerun M1990 semantically with the repaired quota gate.
