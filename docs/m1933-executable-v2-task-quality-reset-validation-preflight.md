# M1933 Executable V2 Task-Quality Reset Validation Preflight

- status: completed
- decision: `task_quality_reset_validation_preflight_pass_route_to_result_audit`
- branch: `paper_route_task_quality_reset_execution`
- summary: `runs/m1933_executable_v2_task_quality_reset_validation_preflight/summary.json`
- input specs: `runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json`
- output dir: `runs/m1933_executable_v2_task_quality_reset_validation_preflight`
- environment reset started: `true`
- rollout/measured execution: `false`
- policy action executed: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1933 ran the frozen reset-only command from M1932:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_reset_validation_preflight \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1933_executable_v2_task_quality_reset_validation_preflight \
  --eval-seed-base 193300 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1934-executable-v2-task-quality-reset-validation-result-audit
```

## Result

Result class:

```text
task_quality_reset_validation_preflight_pass
```

Key counts:

```text
input_executable_spec_count: 80
reset_attempt_count: 80
reset_success_count: 80
reset_failure_count: 0
observation_finite_count: 80
observation_dimension_failure_count: 0
obstacle_initialized_count: 80
contract_violation_count: 0
label_actor_input_violation_count: 0
private_holdout_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
```

Guardrail state:

```text
environment_reset_started: true
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
profile_specific_tuning: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Panel balance after reset:

```text
tier_counts:
  tier_a_positive_support_sanity: 16
  tier_b_feasible_emergency: 16
  tier_c_boundary_near_miss: 16
  tier_d_handling_limit_drift_required: 16
  tier_e_mitigation_only: 16

role_counts:
  stable_aeb: 20
  stable_aes_only: 20
  drift_required_recovery: 20
  unavoidable_mitigation: 20

surface_counts:
  steady_surface: 40
  post_friction_step: 40

sampled_label_counts:
  aeb_feasible: 20
  aes_feasible: 20
  drift_required: 20
  unavoidable: 20
```

## Artifacts

M1933 wrote:

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

`reset_failure_rows.csv` is header-only because no reset failed.

## Interpretation Boundary

M1933 supports:

```text
the M1928 80-spec public task-quality scenario panel is reset-valid under the
current simulator and strict human-view observation contract.
```

M1933 does not support:

- rollout success;
- controller-family ranking;
- policy improvement;
- finite-window vs GRU comparison;
- paper-level benchmark evidence;
- level3 self-identification.

Those claims remain blocked until measured rollout, audit, baselines, multi-seed
evaluation, and mechanism tests are run.

## Next

Next milestone:

```text
m1934-executable-v2-task-quality-reset-validation-result-audit
```

M1934 should audit this reset pass before measured rollout design. It may admit
measured execution design only if the claim boundary remains explicit.
