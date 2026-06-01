# M2107 Paper-Route Outcome-Supported Decisive Public-Gate Core Repaired Measured Execution Command Design

- status: completed
- decision: `public_gate_core_repaired_measured_command_design_route_to_frozen_execution`
- reset/rollout/measured execution in M2107: `false`
- policy actions executed in M2107: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Frozen Command

M2108 must run only this command:

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_routing_smoke_measured_runner \
  --executable-task-specs runs/m2104_paper_route_outcome_supported_decisive_public_gate_core_measured_execution_repair/public_gate_core_measured_repaired_executable_task_specs.json \
  --workload runs/m2104_paper_route_outcome_supported_decisive_public_gate_core_measured_execution_repair/public_gate_core_measured_repaired_workload.csv \
  --output-dir runs/m2108_paper_route_outcome_supported_decisive_public_gate_core_repaired_measured_execution \
  --eval-seed-base 210100 \
  --device cpu \
  --target-episode-count 480 \
  --target-spec-count 96 \
  --target-profile-count 5 \
  --next-blocker m2109-paper-route-outcome-supported-decisive-public-gate-core-repaired-measured-execution-result-audit
```

The repaired workload contains exactly two `eval_seed_override` rows:

```text
m2063-osd-osd_v0_0162_t3::L2_window_50 -> 210260
m2063-osd-osd_v0_0235_t5::L3_online_gru -> 210333
```

All other workload cells must use the default measured-runner behavior:

```text
eval_seed = eval_seed_base + cell_index
```

## Pass/Fail Gates

M2108 passes the execution gate only if:

```text
episode_count == 480
failure_count == 0
spec_count == 96
profile_count == 5
metadata_missing_count == 0
metric_completeness_failure_count == 0
guardrail_violation_count == 0
environment_rollout_started == true
policy_action_executed == true
measured_rollout_started == true
```

M2108 must also keep these false:

```text
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
```

Any nonzero failure rows, metric completeness failures, or guardrail violations
must fail closed and route to M2109 audit. Outcome interpretation and controller
ranking remain blocked until after the result audit.

## Supported Claims

Supported:

```text
The repaired measured execution command is exact, uses M2104 repaired artifacts,
preserves the two audited seed overrides, and has explicit pass/fail gates.
```

Unsupported:

```text
measured execution rerun has completed;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2108-paper-route-outcome-supported-decisive-public-gate-core-repaired-measured-execution-implementation-and-run
```
