# M2090 Paper-Route Outcome-Supported Decisive Reset-Valid Core Reset Validation Command Design

- status: completed
- decision: `reset_valid_core_reset_command_design_route_to_fresh_seed_validator_run`
- parent audit: `docs/m2089-paper-route-outcome-supported-decisive-reset-valid-core-panel-reduction-result-audit.md`
- reduced specs: `runs/m2088_paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction/reset_valid_core_executable_task_specs.json`
- reset execution in M2090: `false`
- rollout/measured execution in M2090: `false`
- policy actions executed in M2090: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2090 freezes the next reset-only validation command over the M2088 reduced
238-row panel. It does not run the command.

The command uses a fresh seed base:

```text
eval_seed_base: 210100
```

This base is outside the M2085 reset evidence seed base:

```text
M2085 eval seed base: 209500
M2091 eval seed base: 210100
```

So M2091 tests the reduced panel under a fresh reset seed base rather than
only relying on the M2085 reset-success rows used to build the panel.

## Frozen Command

M2091 may run only this reset-validation route:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_reset_validation_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight \
  --executable-task-specs runs/m2088_paper_route_outcome_supported_decisive_reset_valid_core_panel_reduction/reset_valid_core_executable_task_specs.json \
  --output-dir runs/m2091_paper_route_outcome_supported_decisive_reset_valid_core_reset_validation_preflight \
  --eval-seed-base 210100 \
  --target-spec-count 238 \
  --expected-observation-dim 72 \
  --next-blocker m2092-paper-route-outcome-supported-decisive-reset-valid-core-reset-validation-result-audit
```

## Pass Gates

M2091 passes reset validation only if:

```text
input_executable_spec_count == 238
target_executable_spec_count == 238
reset_attempt_count == 238
reset_success_count == 238
reset_failure_count == 0
observation_dimension_failure_count == 0
observation_finite_count == 238
obstacle_initialized_count == 238
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
family_quota_pass == true
split_quota_pass == true
difficulty_axis_coverage_pass == true
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
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

Pass or fail, M2091 must route to M2092 result audit before measured execution.

## Claim Boundary

M2090 supports only:

```text
the fresh-seed reset-only validation command for the reduced panel is fully specified.
```

M2090 does not support:

```text
fresh reset validity;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2091-paper-route-outcome-supported-decisive-reset-valid-core-reset-validation-implementation-and-run
```
