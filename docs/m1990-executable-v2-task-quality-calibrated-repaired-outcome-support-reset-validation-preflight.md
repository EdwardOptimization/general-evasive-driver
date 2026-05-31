# M1990 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Reset Validation Preflight

- status: completed
- decision: `task_quality_calibrated_outcome_support_reset_validation_quota_gate_fail_route_to_audit`
- command source: `docs/m1989-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-command-design.md`
- summary: `runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/summary.json`
- environment reset started: `true`
- environment rollout started: `false`
- policy action executed: `false`
- measured execution started: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1990 ran the frozen M1989 reset-only command:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_reset_validation_preflight \
  --executable-task-specs runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight \
  --eval-seed-base 199000 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1991-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-result-audit
```

## Result

M1990 fails the public smoke gate, but the failure is not a reset, contract, or
guardrail failure.

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

Observed source-kind distribution:

```text
anchor_neighborhood: 24
mitigation_isolation_check: 20
offtrack_boundary_relief: 16
success_stabilizer: 20
```

This matches the M1986 selected repair-axis distribution after mapping
`offtrack_anchor_relief -> anchor_neighborhood`,
`mitigation_metric_isolation -> mitigation_isolation_check`,
`offtrack_boundary_relief_extension -> offtrack_boundary_relief`, and
`success_support_expansion -> success_stabilizer`.

The reset validator still uses the older calibrated-materialization quota
expectations:

```text
anchor_neighborhood: 32
mitigation_isolation_check: 16
offtrack_boundary_relief: 8
success_stabilizer: 24
```

Therefore M1990 should be audited as a fail-closed quota-expectation mismatch,
not as evidence that the M1986 executable specs cannot reset.

## Artifacts

```text
runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/summary.json
runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/reset_rows.csv
runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/reset_failure_rows.csv
runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/contract_rows.csv
runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/reset_distribution_by_source_kind.csv
runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/reset_distribution_by_role_surface.csv
runs/m1990_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight/claim_boundary.csv
```

## Supported Claims

Supported narrow claims:

- the frozen M1989 reset-only command ran without environment rollout or policy
  action execution;
- all `80` M1986 executable specs reset successfully;
- all reset observations are finite and have the expected 72-dimensional
  human-view actor observation;
- obstacle initialization succeeds for all `80` specs;
- actor-input contract, label actor-input, forbidden-key, and guardrail counts
  are all `0`.

Unsupported claims:

- M1990 cannot yet claim pass because `result_class` is fail;
- M1990 cannot claim controller-family ranking;
- M1990 cannot claim measured rollout success;
- M1990 cannot claim paper-level benchmark evidence;
- M1990 cannot claim finite-window vs GRU evidence;
- M1990 cannot claim level3 self-identification.

## Next

Next milestone:

```text
m1991-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-result-audit
```

M1991 should audit the quota mismatch before any validator change or rerun.
