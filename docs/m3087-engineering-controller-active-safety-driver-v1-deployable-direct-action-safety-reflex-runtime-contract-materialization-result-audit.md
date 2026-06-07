# M3087 Active Safety Driver v1 Deployable Runtime Contract Result-Audit Synthesis

## Summary

- status: completed
- synthesis decision: `continue`
- decision: `accept_m3086_runtime_contract_route_to_m3088_runtime_smoke_measurement_preflight`
- audited milestone: `m3086-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-contract-materialization-preflight`
- next route: `m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-preflight`

M3087 accepts M3086 as a complete and claim-safe deployable runtime-contract
materialization artifact for the deterministic active-safety reflex layer. It
does not accept M3086 as rollout evidence, validation, ranking, promotion,
repair success, robustness success, driver performance, current-sim verdict,
high-fidelity readiness, paper evidence, finite-window-vs-GRU evidence,
full-driver completion, or self-ID evidence.

The branch should continue, but the next step must be runtime-smoke execution
through the deployable `ActiveSafetyReflexDriver` API, not a performance
verdict. The open safety blockers from M3084 remain active: 5 collision rows,
5 offtrack rows, and 11 speed-too-low rows on the 64-row fresh panel.

## Audited Facts

M3086 recorded:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
driver id: active_safety_reflex_driver_v1_m3078_deterministic
policy_config_sha256: 4e3b185f2f98208b9700280174cf3b4401ae418207da8cb293c72b0c4427d40c
observation_shape: 72
action_shape: 3
action_components: [steer, throttle, brake]
output_semantics: direct_action_clipped
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
driver_interface_rows: 2
driver_action_probe_rows: 5
driver_action_probe_rows_pass: true
actor_input_exclusion_rows: 10
actor_input_exclusion_rows_pass: true
claim_boundary_rows: 21
claim_boundary_rows_pass: true
gate_matrix_rows: 19
environment_reset_run: false
environment_step_run: false
policy_rollout_run: false
validation_run: false
ranking_run: false
checkpoint_promoted: false
```

The materialized deployment contract is:

```text
runtime symbol: autodrift.active_safety_reflex_driver.ActiveSafetyReflexDriver.act
input: finite actor-visible obs72
output: finite bounded action3 [steer throttle brake]
actor_input_contract: actor_visible_obs72_only
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
```

M3086 also preserves the M3084 fresh measurement context in the contract:

```text
fresh rows: 64
fresh failures: 0
fresh success/collision/offtrack/speed_low: 43 / 5 / 5 / 11
fresh clearance_margin_mean: 11.341408769853288
fresh action_clip_fraction_mean: 0.0
```

## evidence_summary

The active-safety direct-action branch has now produced:

```text
M3078: deterministic actor-visible safety-reflex policy contract and rule table
M3080: same-denominator closed-loop measurement, 19/32 success, 3 collision, 3 offtrack, 7 speed-too-low
M3082/M3083: fresh robustness panel materialization and audit, 64 fresh rows, 0 M3080 seed overlap
M3084/M3085: fresh-panel measurement and audit, 43/64 success, 5 collision, 5 offtrack, 11 speed-too-low
M3086/M3087: deployable runtime API and contract audit, obs72 -> [steer throttle brake], no runtime base policy
```

This is meaningful engineering progress toward a deployable active-safety
reflex layer: the actor boundary is clean, the output is direct and bounded,
and the runtime package is callable without a learned base policy or hidden
state. It is not enough to claim validation or robustness success, because the
fresh-panel hard safety failures remain visible.

## supported_claims

M3087 supports only these bounded claims:

```text
M3086 produced complete deployable runtime-contract artifacts
M3086 exposes a callable obs72-to-action3 direct [steer throttle brake] runtime API
M3086 requires no runtime base policy, model checkpoint, or recurrent hidden state
M3086 produced finite bounded action probes for five actor-visible probe frames
M3086 preserved hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor-input exclusion
M3086 preserved M3084 fresh-measurement failure context inside the contract without converting it to a verdict
M3086 kept validation, ranking, promotion, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, repair-success, robustness-result, and self-ID claims out of scope
M3086 is admissible for a bounded runtime-smoke measurement preflight
```

## falsified_claims

M3087 explicitly rejects these claims:

```text
M3086 validates the driver
M3086 proves current-sim driver performance
M3086 proves robustness success
M3086 proves repair success
M3086 justifies ranking, winner selection, checkpoint mutation, or promotion
M3086 establishes high-fidelity readiness
M3086 completes the full ideal driver
M3086 provides paper, finite-window-vs-GRU, or self-ID evidence
M3086 permits hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor input
M3086 permits dropping the 5 collision, 5 offtrack, or 11 speed-too-low M3084 failures from future gates
```

## failure_taxonomy_summary

```text
contract_violation: not observed in M3086; obs72/action3/direct-action/base-policy-free gates pass
lineage_invalid: not observed; M3086 routes from M3085/M3084/M3078 and registers M3087
metric_artifact: not observed for packaging artifacts; action probes and gate rows exist
scenario_sampling_failure: not applicable to M3086 packaging; still unresolved for future runtime-smoke/robustness claims
behavior_regression: not evaluated by M3086; no rollout was run
objective_overfit: active risk if M3086 package probes are treated as deployment readiness
proof_washout: active risk if M3084 success rate is repeated without hard safety failure counts
seed_fragility: not evaluated by M3086; M3084 fresh-seed panel remains the latest behavior evidence
```

## public_gate_overfit_risk

Overfit risk is lower than the earlier fixed-denominator-only path because the
branch has fresh-panel evidence and a deployment API. It is still active:

```text
M3086 probes are synthetic API probes, not closed-loop scenario evidence
M3084 is current-sim fresh measurement, not validation or high-fidelity evidence
M3084 still has collision, offtrack, and speed-too-low failures
```

The next milestone must therefore test runtime integration through the
deployable API and keep all failure counts visible. It must not tune seeds,
change thresholds, rank checkpoints, or convert runtime smoke into a validation
claim.

## next_branch_decision

Continue the branch to exactly one follow-up:

```text
m3088-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-runtime-smoke-measurement-preflight
```

M3088 must run a bounded current-sim runtime smoke using the
`ActiveSafetyReflexDriver` deployable API as the action source. It should verify
that the packaged driver can reset, step, and emit bounded direct action3 values
inside the existing environment contract. It should report collision, offtrack,
speed-too-low, clearance, stability, recovery, and action-pressure fields, but
only as runtime-smoke measurement artifacts.

M3088 must not claim validation, ranking, promotion, driver performance,
current-sim verdict, high-fidelity readiness, paper evidence,
finite-window-vs-GRU evidence, full-driver completion, repair success,
robustness success, or self-ID.

## Boundary

M3087 is a result-audit synthesis only. It runs no reset, step, rollout, replay,
fitting, PPO, training, validation, ranking, promotion, high-fidelity
simulation, finite-window-vs-GRU comparison, or self-ID test.
