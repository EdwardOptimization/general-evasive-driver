# M3126 Residual Hard-Safety Counterfactual Action-Authority Envelope Diagnostic Result Audit

## Decision

- decision: `accept_m3125_envelope_diagnostics_route_to_m3127_trajectory_level_controller_architecture_diagnostic_materialization`
- selected next action: `m3127-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-controller-architecture-diagnostic-materialization-preflight`
- result class: `accept_m3125_counterfactual_action_authority_envelope_diagnostics`

## Evidence Summary

M3125 is complete and claim-safe as a no-new-execution counterfactual action-authority envelope diagnostic:

```text
status_pass: True
gate_matrix_pass: True
required_artifacts_present: True
source M3123 diagnostic rows: 7
source M3115 action influence rows: 7
source M3115 step trace rows: 256
envelope rows: 7
residual collision/offtrack/speed_too_low: 5/2/0
mean final brake margin to full: 0.2776751737509455
mean final steer margin to saturation: 0.10283599155289788
near or full exhausted envelope rows: 6
runtime_base_policy_required: False
```

Envelope status counts:

```text
joint_brake_steer_envelope_exhausted_clearance_unresolved: 3
joint_brake_steer_envelope_near_exhausted_clearance_unresolved: 2
stability_recovery_envelope_timing_limited: 1
stability_steer_envelope_near_exhausted: 1
```

Route recommendation counts:

```text
trajectory_level_controller_architecture_or_feasibility_diagnostic_before_more_direct_gain: 5
trajectory_level_stability_recovery_architecture_diagnostic_before_more_direct_gain: 1
stability_recovery_timing_or_trajectory_level_controller_diagnostic: 1
```

## Accepted Claims

- M3125 artifacts are complete and claim-safe.
- M3125 preserves row identity for all seven residual hard-safety rows.
- M3125 preserves the actor contract: obs72 to direct action3 `[steer, throttle, brake]`, with `runtime_base_policy_required: False`.
- The residual blocker set remains 5 collision and 2 offtrack with 0 speed-too-low.
- Six of seven residual rows are already near or fully exhausted under the M3125 envelope labels, so another blind local direct-gain edit is not justified by the current evidence.
- The next route should materialize a trajectory-level/controller-architecture diagnostic before any repair implementation or measurement.

## Rejected Claims

- M3125 is not repair-success evidence.
- M3125 is not validation, ranking, promotion, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, or self-ID evidence.
- M3125 does not prove feasibility or infeasibility of the residual rows.
- M3125 does not justify another direct-rule gain edit by itself.
- M3125 does not authorize checkpoint mutation, checkpoint promotion, or winner selection.

## Failure Taxonomy

- `contract_violation`: not observed.
- `lineage_invalid`: not observed.
- `metric_artifact`: not observed.
- `scenario_sampling_failure`: not observed.
- `behavior_regression`: residual objective remains failed because 5 collision and 2 offtrack persist.
- `objective_overfit`: high risk if the branch returns to local direct gains without architecture evidence.
- `proof_washout`: high risk if envelope labels are described as success, feasibility proof, or performance evidence.
- `seed_fragility`: unresolved; no validation or generalization claim is allowed.

## Next

Route to M3127. M3127 should materialize a no-new-execution trajectory-level/controller-architecture diagnostic from M3125 and M3115 artifacts. It should compare candidate architecture families and output contract requirements while preserving direct `[steer, throttle, brake]` deployment semantics and forbidding hidden oracle inputs. It must not implement a repair or run validation.
