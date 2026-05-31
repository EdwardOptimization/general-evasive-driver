# M2072 Paper-Route Outcome-Supported Decisive Repaired Reset Validation Command Design

- status: completed
- decision: `outcome_supported_decisive_repaired_reset_command_design_route_to_existing_validator_run`
- parent audit: `docs/m2071-paper-route-outcome-supported-decisive-reset-materialization-repair-result-audit.md`
- repaired specs: `runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repaired_executable_task_specs.json`
- reset execution in M2072: `false`
- rollout/measured execution in M2072: `false`
- policy actions executed in M2072: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2072 freezes the exact reset-validation route for the M2070 repaired
outcome-supported decisive `240`-spec panel. It does not run reset.

Target:

```text
input executable task specs: 240
reset attempts: 240
expected observation dimension: 72
rollout steps: 0
policy actions: 0
```

The existing focused validator is compatible:

```text
autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight
```

Reason:

```text
M2070 writes the same executable_task_specs JSON payload shape used by M2063,
with additional repair audit fields. The focused reset validator preserves the
candidate metadata it needs and ignores extra fields.
```

## M2073 Command

M2073 should run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_reset_validation_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight \
  --executable-task-specs runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repaired_executable_task_specs.json \
  --output-dir runs/m2073_paper_route_outcome_supported_decisive_repaired_reset_validation_preflight \
  --eval-seed-base 207300 \
  --target-spec-count 240 \
  --expected-observation-dim 72 \
  --next-blocker m2074-paper-route-outcome-supported-decisive-repaired-reset-validation-result-audit
```

## M2073 Pass Gates

M2073 passes only if:

```text
result_class == outcome_supported_decisive_reset_validation_preflight_pass
input_executable_spec_count == 240
target_executable_spec_count == 240
reset_attempt_count == 240
reset_success_count == 240
reset_failure_count == 0
observation_finite_count == 240
observation_dimension_failure_count == 0
obstacle_initialized_count == 240
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
family_quota_pass == true
split_quota_pass == true
difficulty_axis_coverage_pass == true
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
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
```

If M2073 fails, it must fail closed and route to result audit. It must not
repair and rerun inside the same milestone.

## Claim Boundary

If M2073 passes, it may claim only:

```text
the M2070 repaired outcome-supported decisive smoke-proxy panel is reset-valid
under the current simulator and strict human-view observation contract.
```

It still cannot claim:

```text
rollout success;
measured execution success;
controller-family ranking;
finite-window-vs-GRU comparison;
paper-level benchmark evidence;
paper-valid generated task semantics;
level3 self-identification.
```

## Next

Next milestone:

```text
m2073-paper-route-outcome-supported-decisive-repaired-reset-validation-implementation-and-run
```
