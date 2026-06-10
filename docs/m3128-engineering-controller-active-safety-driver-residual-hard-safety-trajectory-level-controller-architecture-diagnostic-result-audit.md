# M3128 Residual Hard-Safety Trajectory-Level Controller Architecture Diagnostic Result Audit

## Decision

- decision: `accept_m3127_architecture_diagnostics_route_to_m3129_trajectory_level_clearance_stability_corridor_reflex_materialization`
- selected next action: `m3129-engineering-controller-active-safety-driver-residual-hard-safety-trajectory-level-clearance-stability-corridor-reflex-materialization-preflight`
- result class: `accept_m3127_trajectory_level_controller_architecture_diagnostics`

## Evidence Summary

M3127 is complete and claim-safe as a no-new-execution architecture diagnostic materialization:

```text
status_pass: True
gate_matrix_pass: True
required_artifacts_present: True
architecture candidate rows: 7
controller contract requirement rows: 10
residual collision/offtrack/speed_too_low: 5/2/0
actor observation contract: obs72_actor_visible_current_frame_only
candidate output semantics: direct_action_clipped
candidate output components: [steer, throttle, brake]
runtime_base_policy_required: False
checkpoint_model_required: False
recurrent_hidden_state_required: False
hidden_oracle_actor_input_required: False
ttc_actor_input_required: False
```

Architecture family counts:

```text
actor_visible_receding_horizon_clearance_corridor_reflex: 5
actor_visible_stability_corridor_recovery_reflex: 1
actor_visible_stability_timing_reflex: 1
```

Controller mode counts:

```text
short_horizon_clearance_timing_and_lateral_offset_scheduler: 5
short_horizon_edge_and_sideslip_recovery_scheduler: 1
short_horizon_sideslip_phase_and_edge_margin_scheduler: 1
```

## Accepted Claims

- M3127 artifacts are complete and claim-safe.
- M3127 preserves row identity for all seven residual hard-safety rows.
- M3127 preserves the deployable actor contract: actor-visible obs72 input to direct `[steer, throttle, brake]` output.
- M3127 rejects hidden oracle, TTC actor input, runtime base policy, checkpoint model, and recurrent hidden-state dependencies.
- M3127 supports a controlled materialization route for a trajectory-level clearance/stability corridor reflex before any measurement.

## Rejected Claims

- M3127 is not a controller implementation.
- M3127 is not repair-success evidence.
- M3127 is not validation, ranking, promotion, robustness-result, driver-performance, current-sim verdict, high-fidelity, paper, full-driver, or self-ID evidence.
- M3127 does not prove feasibility or infeasibility of the residual rows.
- M3127 does not authorize checkpoint mutation, checkpoint promotion, winner selection, or measurement claims.

## Failure Taxonomy

- `contract_violation`: not observed.
- `lineage_invalid`: not observed.
- `metric_artifact`: not observed.
- `scenario_sampling_failure`: not observed.
- `behavior_regression`: residual objective remains failed because 5 collision and 2 offtrack persist.
- `objective_overfit`: medium risk if the next implementation is tuned only to the seven public residual rows without preserving broader fresh-panel gates.
- `proof_washout`: high risk if architecture rows are described as measured safety improvement.
- `seed_fragility`: unresolved; no validation or generalization claim is allowed.

## Next

Route to M3129. M3129 should materialize, but not measure, a deployable trajectory-level clearance/stability corridor reflex contract and deterministic rule artifacts. It must preserve obs72 actor-visible input, direct `[steer, throttle, brake]` output, no runtime base policy, no checkpoint model, no recurrent hidden state, no hidden oracle actor inputs, and no TTC actor-input shortcut. M3129 must register M3130 result audit before any full-fresh measurement or repair-success interpretation.
