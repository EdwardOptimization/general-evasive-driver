# M3136 Guarded Fallback Hybrid Materialization Result Audit

## Decision

- decision: `accept_m3135_guarded_fallback_hybrid_materialization_route_to_m3137_full_fresh_measurement`
- selected next action: `m3137-engineering-controller-active-safety-driver-residual-hard-safety-regression-aware-guarded-fallback-hybrid-full-fresh-measurement-preflight`
- result class: `accept_m3135_complete_claim_safe_guarded_hybrid_materialization`

## Evidence Summary

M3135 is complete and claim-safe as a guarded fallback hybrid materialization artifact:

```text
status_pass: True
gate_matrix_pass: True
required_artifacts_present: True
rule rows: 9
runtime contract rows: 5
actor-input exclusion rows: 12
claim boundary rows: 23
action probe rows: 5
fallback probe rows: 4
bounded mix probe rows: 1
runtime driver id: m3135_regression_aware_guarded_fallback_hybrid
fallback policy id: m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair
corridor policy id: m3129_trajectory_level_clearance_stability_corridor_reflex
runtime_base_policy_required: False
checkpoint_model_required: False
recurrent_hidden_state_required: False
hidden_oracle_actor_input_required: False
ttc_actor_input_required: False
```

Probe behavior is consistent with the M3133 regression decomposition:

```text
clear nominal: fallback path
low speed floor: fallback path
urgent edge: fallback path
sideslip recovery: fallback path
urgent obstacle left: bounded corridor mix alpha 0.025925916654092326
```

## Accepted Claims

- M3135 artifacts are complete and claim-safe.
- M3135 preserves the deployable actor contract: actor-visible obs72 current-frame input to direct `[steer, throttle, brake]` output.
- M3135 defaults to the M3105/M3103 no-regression direct-action path when speed-floor, edge, stability, or obstacle-urgency guards block corridor mixing.
- M3135 only materializes a bounded corridor-style mix in the urgent-obstacle probe and keeps the final action finite and bounded.
- M3135 supports exactly one constrained full-fresh measurement route before any behavior interpretation.

## Rejected Claims

- M3135 is not repair-success evidence.
- M3135 is not validation, ranking, promotion, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, finite-window-vs-GRU, full-driver, feasibility-proof, or self-ID evidence.
- M3135 does not prove the guarded hybrid improves M3105 or M3131.
- M3135 does not justify promotion before a full-fresh measurement and result audit.
- M3135 does not use M3133 row labels, M3105 outcomes, source labels, route labels, verdict labels, hidden oracle values, or TTC as runtime actor inputs.

## Failure Taxonomy

- `contract_violation`: not observed.
- `lineage_invalid`: not observed.
- `metric_artifact`: not observed.
- `scenario_sampling_failure`: not observed.
- `behavior_regression`: unresolved until M3137 measurement.
- `objective_overfit`: controlled by fallback and regression guards but unresolved until M3137 measurement.
- `proof_washout`: high risk if M3135 is described as a measured repair result.
- `seed_fragility`: unresolved; no validation or robustness claim is allowed.

## Next

Route to M3137 full-fresh measurement. M3137 should execute the M3135 guarded fallback hybrid direct-action function on the complete M3084 64-row fresh denominator and write same-row comparisons against M3105, M3095, M3100, and M3090. It must preserve the actor-visible obs72 to direct `[steer, throttle, brake]` contract and must not claim validation, ranking, promotion, driver performance, current-sim verdict, robustness result, high-fidelity result, repair success, feasibility proof, or self-ID evidence.
