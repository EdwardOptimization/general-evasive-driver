# M2100 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Execution Command Design

- status: completed
- decision: `public_gate_core_measured_command_design_route_to_frozen_execution`
- manifest: `experiments/manifests/m2100-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-command-design.json`
- parent audit: `docs/m2099-paper-route-outcome-supported-decisive-public-gate-core-measured-runner-compatibility-repair-result-audit.md`
- executable specs: `runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair/public_gate_core_measured_compatible_executable_task_specs.json`
- planned workload: `runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair/public_gate_core_measured_compatible_workload.csv`
- measured execution in M2100: `false`
- rollout/policy actions in M2100: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2100 freezes the measured-execution command for the M2098
metadata-compatible public-gate core workload. It does not run rollout or policy
actions.

Target execution scope:

```text
executable task specs: 96
controller profiles: 5
planned workload rows: 480
eval_seed_base: 210100
device: cpu
```

## Runner

Use the existing focused measured runner:

```text
autodrift.paper_route_controlled_routing_smoke_measured_runner
```

M2098 already repaired the required runner metadata and verified:

```text
measured_runner_validation_failure_count: 0
env_config_changed_count: 0
duplicate_workload_id_count: 0
guardrail_violation_count: 0
```

## M2101 Command

M2101 should run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_controlled_routing_smoke_measured_runner.py
```

Then:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_measured_runner \
  --executable-task-specs runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair/public_gate_core_measured_compatible_executable_task_specs.json \
  --workload runs/m2098_paper_route_outcome_supported_decisive_public_gate_core_measured_runner_compatibility_repair/public_gate_core_measured_compatible_workload.csv \
  --output-dir runs/m2101_paper_route_outcome_supported_decisive_public_gate_core_measured_execution \
  --eval-seed-base 210100 \
  --device cpu \
  --target-episode-count 480 \
  --target-spec-count 96 \
  --target-profile-count 5 \
  --next-blocker m2102-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-result-audit
```

## Pass Gates

M2101 passes only if:

```text
result_class == controlled_routing_smoke_measured_execution_pass
episode_count == 480
target_episode_count == 480
failure_count == 0
spec_count == 96
target_spec_count == 96
profile_count == 5
target_profile_count == 5
metadata_missing_count == 0
family_quota_pass == true
source_kind_quota_pass == true
proxy_template_quota_pass == true
generated_proxy_quota_pass == true
metric_completeness_failure_count == 0
guardrail_violation_count == 0
environment_rollout_started == true
policy_action_executed == true
measured_rollout_started == true
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

If validation fails before rollout, M2101 must fail closed with
`episode_count=0` and write `validation_failure_rows.csv`. If rollout failures
occur, they must be preserved in `failure_rows.csv` and interpreted only in the
M2102 result audit.

## Claim Boundary

M2101 measured execution, even if complete, may claim only:

```text
the public-gate core workload was executed and produced complete measured
rollout artifacts.
```

It cannot claim:

```text
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
paper-valid generated task semantics;
level3 self-identification.
```

## Next

Next milestone:

```text
m2101-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-implementation-and-run
```

M2101 may run only the frozen measured-execution command. Interpretation must
be deferred to M2102 result audit.
