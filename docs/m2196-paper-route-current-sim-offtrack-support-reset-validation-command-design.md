# M2196 Paper-Route Current-Sim Offtrack-Support Reset-Validation Command Design

- status: completed
- decision: `current_sim_offtrack_support_reset_validation_command_design_admit_compatibility_implementation_and_run`
- manifest: `experiments/manifests/m2196-paper-route-current-sim-offtrack-support-reset-validation-command-design.json`
- parent materialization audit: `docs/m2195-paper-route-current-sim-offtrack-support-candidate-materialization-result-audit.md`
- parent repaired specs: `runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json`
- next manifest: `experiments/manifests/m2197-paper-route-current-sim-offtrack-support-reset-validation-compatibility-implementation-and-run.json`
- implementation in M2196: `false`
- reset in M2196: `false`
- measured execution in M2196: `false`
- policy action executed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2196 should not run the old reset validator unchanged. The validator currently
hard-codes the original M2151 materialization semantics and paper validity
status, while M2194 repaired specs use offtrack-support-specific semantics.

Required compatibility extension:

```text
--expected-materialization-semantics current_sim_offtrack_support_repair_materialization_v0
--expected-paper-validity-status current_sim_offtrack_support_candidate_not_reset_validated
--task-id m2197-paper-route-current-sim-offtrack-support-reset-validation-compatibility-implementation-and-run
```

The extension must preserve the default M2151 values when those flags are not
provided, so older reset-validation workflows remain backward compatible.

## Command To Implement

M2197 should implement the compatibility flags and run:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight \
  --executable-task-specs runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json \
  --output-dir runs/m2197_paper_route_current_sim_offtrack_support_reset_validation_preflight \
  --eval-seed-base 219700 \
  --target-spec-count 288 \
  --expected-observation-dim 72 \
  --seed-source-mode prefer_spec_eval_seed_override \
  --expected-materialization-semantics current_sim_offtrack_support_repair_materialization_v0 \
  --expected-paper-validity-status current_sim_offtrack_support_candidate_not_reset_validated \
  --task-id m2197-paper-route-current-sim-offtrack-support-reset-validation-compatibility-implementation-and-run \
  --next-blocker m2198-paper-route-current-sim-offtrack-support-reset-validation-result-audit
```

This command is reset-only. It must not step environments after reset and must
not execute policy actions.

## Expected Result Contract

M2197 should pass only if:

```text
input_executable_spec_count: 288
target_executable_spec_count: 288
reset_attempt_count: 288
reset_success_count: 288
reset_failure_count: 0
expected_observation_dim: 72
observation_dimension_failure_count: 0
observation_finite_count: 288
obstacle_initialized_count: 288
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
seed_source_mode: prefer_spec_eval_seed_override
seed_source_quota_pass: true
guardrail_violation_count: 0
```

Expected claim boundary:

```text
reset_validity: admissible only if all reset checks pass
controller_family_ranking: false
winner_selection: false
finite_window_vs_gru_conclusion: false
paper_level_benchmark_evidence: false
level3_self_identification: false
```

## Compatibility Implementation Requirements

The reset validator should be changed narrowly:

```text
contract_row_for_spec(spec, expected_materialization_semantics, expected_paper_validity_status)
run_current_sim_reset_validation_preflight(... expected_materialization_semantics, expected_paper_validity_status, task_id)
CLI flags for both expected strings and task_id
summary records the expected strings and task_id
run_state uses task_id instead of hard-coded M2154 id
```

Do not relax:

```text
history_length >= 1
action_history_mode = full
include_privileged_params = false
wheel_observation_mode = none
obstacle_relative_velocity_mode = zero
obstacle.enabled = true
obstacle.max_sample_attempts >= 200
actor_input_contract = P0_human_view_no_wheel_no_oracle
forbidden-key scan
no policy-action / no rollout guardrails
```

## Next Step

M2197 may implement the compatibility flags, add focused tests for both default
M2151 semantics and M2194 semantics, and then run the reset-only validation.

Still blocked:

```text
measured execution
controller-family ranking
winner selection
finite-window vs GRU verdict
paper-level benchmark evidence
level3 self-identification
```
