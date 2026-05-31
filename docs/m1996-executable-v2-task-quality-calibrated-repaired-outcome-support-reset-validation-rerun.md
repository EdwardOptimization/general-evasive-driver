# M1996 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Reset Validation Rerun

- status: completed
- decision: `task_quality_calibrated_outcome_support_repaired_reset_validation_pass_route_to_result_audit`
- command source: `docs/m1995-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-command-design.md`
- summary: `runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/summary.json`
- environment reset started: `true`
- environment rollout started: `false`
- policy action executed: `false`
- measured execution started: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1996 ran the frozen M1995 repaired reset-only command:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_reset_validation_preflight \
  --executable-task-specs runs/m1986_executable_v2_task_quality_calibrated_outcome_support_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired \
  --eval-seed-base 199600 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1997-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-result-audit
```

## Result

M1996 passes the repaired reset-validation gate:

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
expected_quota_source: executable_task_specs
quota_metadata_missing_count: 0
source_kind_quota_pass: true
role_surface_quota_pass: true
guardrail_violation_count: 0
passes_public_smoke_gates: true
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

Source-kind distribution:

```text
anchor_neighborhood: 24
mitigation_isolation_check: 20
offtrack_boundary_relief: 16
success_stabilizer: 20
```

Quota metadata missing rows:

```text
0
```

## Artifacts

```text
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/summary.json
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/reset_rows.csv
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/reset_failure_rows.csv
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/contract_rows.csv
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/reset_distribution_by_source_kind.csv
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/reset_distribution_by_role_surface.csv
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/quota_metadata_missing_rows.csv
runs/m1996_executable_v2_task_quality_calibrated_repaired_outcome_support_reset_validation_preflight_repaired/claim_boundary.csv
```

## Supported Claims

M1996 supports:

- the repaired M1986 outcome-support executable panel is reset-valid;
- all `80` specs reset with finite 72-dimensional human-view observations;
- obstacle initialization succeeds for all `80` specs;
- actor-input contract, label actor-input, forbidden-key, and guardrail counts
  are all `0`;
- artifact-driven source-kind and role-surface quota checks pass;
- the stale quota metric artifact from M1990 is repaired for this reset gate.

M1996 does not support:

- measured rollout success;
- controller-family ranking;
- finite-window vs GRU comparison;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification.

## Next

Next milestone:

```text
m1997-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-validation-rerun-result-audit
```

M1997 should audit the pass before measured execution command design.
