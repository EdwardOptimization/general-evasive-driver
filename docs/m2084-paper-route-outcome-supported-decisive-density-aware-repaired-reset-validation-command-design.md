# M2084 Paper-Route Outcome-Supported Decisive Density-Aware Repaired Reset Validation Command Design

- status: completed
- decision: `density_aware_repaired_reset_command_design_route_to_fresh_seed_validator_run`
- parent audit: `docs/m2083-paper-route-outcome-supported-decisive-density-aware-obstacle-filter-repair-result-audit.md`
- repaired specs: `runs/m2082_paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight/density_aware_repaired_executable_task_specs.json`
- reset execution in M2084: `false`
- rollout/measured execution in M2084: `false`
- policy actions executed in M2084: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Decision

M2084 freezes the next reset-only validation command over the M2082
density-aware repaired specs. It does not run the command.

The command uses a fresh seed base:

```text
eval_seed_base: 209500
```

This base is outside both the M2079 reset seed base and the M2082 targeted
support seed panel:

```text
M2079 eval seeds for failed rows:
  207900 + task_index

M2082 support seeds for failed rows:
  M2079 failing eval_seed + [0, 240, 480, 720, 960]

largest targeted support seed:
  207900 + 200 + 960 = 209060

M2085 eval seed base:
  209500
```

So M2085 will test fresh reset sampling rather than replaying the no-reset
density-support panel.

## Frozen Command

M2085 may run only this reset-validation route:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_reset_validation_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_reset_validation_preflight \
  --executable-task-specs runs/m2082_paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight/density_aware_repaired_executable_task_specs.json \
  --output-dir runs/m2085_paper_route_outcome_supported_decisive_density_aware_repaired_reset_validation_preflight \
  --eval-seed-base 209500 \
  --target-spec-count 240 \
  --expected-observation-dim 72 \
  --next-blocker m2086-paper-route-outcome-supported-decisive-density-aware-repaired-reset-validation-result-audit
```

## Pass Gates

M2085 passes reset validation only if:

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

Pass or fail, M2085 must route to M2086 result audit before measured execution.

## Stop Rule

M2085 is the decisive reset-validation rerun for this local repair branch:

```text
If scenario sampling still fails, M2086 must synthesize and stop, pivot, or
reduce the panel. It must not route to another local obstacle-filter repair.
```

## Claim Boundary

M2084 supports only:

```text
the fresh-seed reset-only validation command is fully specified.
```

M2084 does not support:

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
m2085-paper-route-outcome-supported-decisive-density-aware-repaired-reset-validation-implementation-and-run
```
