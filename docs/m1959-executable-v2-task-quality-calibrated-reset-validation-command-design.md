# M1959 Executable V2 Task-Quality Calibrated Reset Validation Command Design

- status: completed
- decision: `task_quality_calibrated_reset_command_design_admit_focused_reset_validator`
- branch: `paper_route_task_quality_calibrated_materialization`
- parent preflight: `docs/m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation.md`
- executable specs: `runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json`
- reset execution in M1959: `false`
- rollout/measured execution in M1959: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M1959 freezes the reset-only validation route for the M1958 calibrated
executable specs. It does not run reset. The next milestone may run reset-only
validation if it uses the exact command and pass gates below.

Target:

```text
input executable task specs: 80
reset attempts: 80
expected observation dimension: 72
rollout steps: 0
policy actions: 0
```

## Validator Decision

Use a focused calibrated reset validator for M1960:

```text
autodrift.executable_v2_task_quality_calibrated_reset_validation_preflight
```

The existing generic reset validator can rebuild env configs and reset them,
but its output schema is tied to the older task-quality panel fields such as
`feasibility_tier_id` and `surface_variant`. The M1958 specs carry calibrated
repair-wave metadata:

```text
repair_source_kind
selection_quota_name
parent_feasibility_tier_id
parent_surface_variant
normalized_surface_variant
base_geometry_source
representative_cell_rule
```

M1960 should preserve those fields in reset rows and aggregates rather than
dropping them during validation.

## M1960 Command

M1960 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_reset_validation_preflight \
  --executable-task-specs runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json \
  --output-dir runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight \
  --eval-seed-base 196000 \
  --target-spec-count 80 \
  --expected-observation-dim 72 \
  --next-blocker m1961-executable-v2-task-quality-calibrated-reset-validation-result-audit
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_task_quality_calibrated_reset_validation_preflight.py
```

## Expected Artifacts

M1960 must write:

```text
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/summary.json
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_rows.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_failure_rows.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/contract_rows.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_distribution_by_source_kind.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/reset_distribution_by_role_surface.csv
runs/m1960_executable_v2_task_quality_calibrated_reset_validation_preflight/claim_boundary.csv
```

Each reset row must preserve:

```text
task_source_id
candidate_source_id
repair_candidate_id
repair_source_kind
selection_quota_name
source_role_semantics
parent_feasibility_tier_id
parent_surface_variant
normalized_surface_variant
source_split
base_geometry_source
representative_cell_rule
sampled_obstacle_label
obstacle_distance
obstacle_half_width
eval_seed
reset_success
observation_length
observation_finite
obstacle_initialized
environment_reset_started
environment_rollout_started
policy_action_executed
```

## M1960 Pass Gates

M1960 passes only if:

```text
result_class == task_quality_calibrated_reset_validation_preflight_pass
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
forbidden_key_violation_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
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

If any reset fails, M1960 must fail closed and route to result/failure audit. It
must not repair and rerun inside the same milestone.

## Failure Taxonomy

M1960 should classify reset failures as:

```text
schema_incompatible
env_config_rebuild_failure
human_view_contract_violation
reset_sampling_failure
observation_contract_failure
metadata_join_failure
guardrail_violation
```

Any reset failure is task-quality scenario evidence, not controller-family
evidence. Controller ranking remains blocked until reset validation passes and
a measured execution route is separately designed.

## Claim Boundary

If M1960 passes, it may claim only:

```text
the M1958 calibrated 80-spec public diagnostic panel is reset-valid under the
current simulator and strict human-view observation contract.
```

It still cannot claim:

- rollout success;
- measured execution success;
- controller-family ranking;
- policy improvement;
- finite-window vs GRU comparison;
- level3 self-identification;
- paper-level benchmark evidence.

## Next

Next milestone:

```text
m1960-executable-v2-task-quality-calibrated-reset-validation-preflight
```

M1960 may run the frozen reset-only command. Interpretation must be deferred to
M1961 result audit.
