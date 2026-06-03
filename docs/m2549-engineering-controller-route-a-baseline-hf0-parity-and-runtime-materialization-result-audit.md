# M2549 Engineering Controller Route A Baseline HF0 Parity And Runtime Materialization Result Audit

- status: completed
- decision: `accept_route_a_hf0_parity_runtime_materialization_route_to_result_synthesis`
- manifest: `experiments/manifests/m2549-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-result-audit.json`
- audited summary: `runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json`
- audited milestone doc: `docs/m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight.md`
- follow-up manifest: `experiments/manifests/m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis.json`
- next: `m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis`

## Audit Inputs

M2549 reads M2548 HF0 parity/runtime artifacts only. It does not run a
new environment step, execute policy action, train, replay, rank, promote,
compute success rates, or claim validation.

Audited artifacts:

```text
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/hf0_p0_parity_checks.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/action_mapping_checks.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/runtime_report_schema.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/actor_inference_cost_rows.csv
runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/materialization_gate_matrix.csv
docs/m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight.md
```

## Findings

M2548 passes the pre-registered materialization gates:

```text
status_pass: true
result_class: engineering_controller_route_a_hf0_parity_runtime_materialization_pass
source_artifacts_exist: true
hf0_p0_parity_check_count: 5
hf0_p0_parity_checks_all_pass: true
action_mapping_check_count: 7
action_mapping_checks_all_pass: true
runtime_schema_field_count: 21
actor_inference_cost_row_count: 270
expected_actor_inference_cost_row_count: 270
materialization_gate_count: 8
materialization_gates_all_pass: true
all_policy_checkpoints_admitted: true
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
```

Parity audit:

- default actor-view extraction passes
- current-sim reset and canned-step extraction pass
- four-wheel HF0 source-only reset and canned-step extraction pass
- all rows preserve P0 observation shape `72`
- diagnostics-only keys are checked and remain outside actor input

Action mapping audit:

- valid actions preserve deployed action shape `3`
- out-of-range finite actions clip to `[-1, 1]`
- throttle/brake physical-control mapping stays normalized into `[0, 1]`
- invalid-shape and non-finite actions are rejected

Runtime audit:

- subjects: M1154 original, M2532 guarded repair, M2537 mitigation-preserving repair
- all three policy checkpoints are admitted under P0 `72/3`
- actor encoder is `human_view_online_gru`
- action sequence horizon is `1`
- batch sizes are `1`, `8`, and `32`
- measured iterations are `30`
- actor inference cost row count is `270`
- all runtime rows have observation shape `72`, action shape `3`, finite bounded actor outputs, and positive forward time

Claim-boundary audit:

- no external high-fidelity simulator was installed, imported, or run
- no policy rollout was run
- actor outputs were not interpreted as deployed control performance
- no training, replay, PPO, ranking, winner selection, checkpoint promotion, success-rate, validation, driver-performance, paper, FW-vs-GRU, current-sim, high-fidelity validation, or level3 self-ID claim is made

## Accepted Claim

M2549 accepts M2548 as a source-level Route A HF0 parity/runtime
materialization artifact. It proves the interface and runtime-report
artifact chain is materialized and internally consistent.

## Rejected Claims

M2549 rejects treating M2548 as:

- controller ranking
- checkpoint promotion
- success-rate verdict
- driver-performance validation
- high-fidelity validation readiness or result
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU evidence
- level3 self-identification evidence

## Decision

Route to M2550 result synthesis. The synthesis should decide the next bounded
HF0/HF1 route from accepted parity/runtime readiness evidence without
promoting it to validation or performance.
