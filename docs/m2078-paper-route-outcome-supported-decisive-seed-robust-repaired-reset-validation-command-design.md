# M2078 Paper-Route Outcome-Supported Decisive Seed-Robust Repaired Reset Validation Command Design

- status: completed
- decision: `seed_robust_repaired_reset_command_design_route_to_fresh_seed_validator_run`
- parent audit: `docs/m2077-paper-route-outcome-supported-decisive-seed-robust-obstacle-filter-repair-result-audit.md`
- repaired specs: `runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_robust_repaired_executable_task_specs.json`
- reset execution in M2078: `false`
- rollout/measured execution in M2078: `false`
- policy actions executed in M2078: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2078 freezes the next reset-only validation command over the M2076
seed-robust repaired specs. It does not run the command.

The command uses a fresh seed base:

```text
eval_seed_base: 207900
```

This base is outside the M2076 support seed panel:

```text
M2076 support seeds per spec:
  207300 + task_index
  207540 + task_index
  207780 + task_index
  208020 + task_index
  208260 + task_index
```

So M2079 will test fresh reset sampling rather than replaying the no-reset
support seeds.

## Frozen Command

M2079 may run only this reset-validation route:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_reset_validation_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight \
  --executable-task-specs runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_robust_repaired_executable_task_specs.json \
  --output-dir runs/m2079_paper_route_outcome_supported_decisive_seed_robust_repaired_reset_validation_preflight \
  --eval-seed-base 207900 \
  --target-spec-count 240 \
  --expected-observation-dim 72 \
  --next-blocker m2080-paper-route-outcome-supported-decisive-seed-robust-repaired-reset-validation-result-audit
```

## Pass Gates

M2079 passes reset validation only if:

```text
input_executable_spec_count == 240
target_executable_spec_count == 240
reset_attempt_count == 240
reset_success_count == 240
reset_failure_count == 0
observation_dimension_failure_count == 0
observation_finite_count == 240
obstacle_initialized_count == 240
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

Pass or fail, M2079 must route to M2080 result audit before measured execution.

## Claim Boundary

M2078 supports only:

```text
the fresh-seed reset-only validation command is fully specified.
```

M2078 does not support:

```text
reset validity;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2079-paper-route-outcome-supported-decisive-seed-robust-repaired-reset-validation-implementation-and-run
```
