# M2649 Engineering Controller Route A Source-Only Gap-Targeted Repair Execution Result Audit

- status: completed
- decision: `accept_m2648_route_to_protected_mitigation_regression_localization`
- manifest: `experiments/manifests/m2649-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-execution-result-audit.json`
- parent summary: `runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/summary.json`
- parent gate rows: `runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/repair_gate_evaluation.csv`
- parent behavior rows: `runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/post_repair_behavior_rows.csv`
- parent checkpoint manifest: `runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/repaired_checkpoint_manifest.json`
- follow-up manifest: `experiments/manifests/m2650-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-protected-mitigation-regression-localization-preflight.json`
- next: `m2650-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-protected-mitigation-regression-localization-preflight`

## Audit Result

M2649 accepts M2648 as bounded Route A source-only gap-targeted repair
execution evidence for audit. It rejects any ranking, promotion,
success-rate, validation, driver-performance, paper, finite-window-vs-GRU,
current-sim, high-fidelity validation, full ideal driver, or self-ID
interpretation.

Accepted M2648 summary:

```text
status_pass: true
result_class: engineering_controller_route_a_source_only_gap_targeted_repair_execution_preflight_pass
repair_execution_started: true
repair_training_started: true
training_run: true
training_observation_count: 24
repaired_checkpoint_written: true
checkpoint_behavior_changed: true
post_repair_behavior_row_count: 160
telemetry_row_count: 12800
repair_gate_evaluation_row_count: 7
actor_contract_shape_72_action_3: true
hidden_or_oracle_actor_inputs_required: false
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
checkpoint_promoted: false
ranking_run: false
winner_selected: false
success_rate_computed: false
driver_performance_claim_made: false
```

M2648 wrote all required artifacts:

```text
repair_config_snapshot.json
repair_training_trace.csv
repaired_checkpoint_manifest.json
post_repair_behavior_rows.csv
repair_gate_evaluation.csv
summary.json
milestone doc
```

The checkpoint manifest is traceable and not promoted:

```text
source_checkpoint: runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/checkpoints/m2537_mitigation_preserving_actor_head_repair.pt
repaired_checkpoint: runs/m2648_engineering_controller_route_a_source_only_gap_targeted_repair_execution/checkpoints/m2648_gap_targeted_actor_head_repair.pt
update_method: deterministic_gap_targeted_actor_head_bias_projection
trainable_parameter_names: actor_mean.bias[0], actor_mean.bias[1], actor_mean.bias[2]
behavior_changed: true
checkpoint_promoted: false
hidden_or_oracle_actor_inputs_required: false
active_config_overwritten: false
taxonomy_artifacts_mutated: false
repair_design_mutated: false
```

## Gate Audit

M2648 target gates passed:

```text
target_road_boundary_margin_control:
  target family: road_departure_dominant_gap
  evaluated rows: 16
  improved rows: 16
  regressed rows: 0
  gate_pass: true

target_drift_collision_recovery_tradeoff:
  target family: drift_recovery_mixed_gap
  evaluated rows: 8
  improved rows: 8
  regressed rows: 0
  gate_pass: true
```

M2648 protected gates:

```text
protected_axis_diagnostic_only:
  evaluated rows: 160
  gate_pass: true

protected_mitigation_reference:
  target/reference family: mitigation_collision_saturated_reference
  evaluated rows: 8
  improved rows: 7
  regressed rows: 1
  gate_pass: false
  failure_type: behavior_regression
```

Contract and claim-boundary gates passed:

```text
contract_p0_72_3: true
no_oracle_actor_inputs: true
no_ranking_no_success_rate: true
```

## Protected Mitigation Regression

The protected mitigation blocker is confirmed. The single regressed row is:

```text
subject: m2537_mitigation_preserving_policy
scenario_role: unavoidable_mitigation
seed: 267101
dynamics_axis_id: fresh_fault_delay_noise
severity_proxy: 3.953864 -> 3.987916
severity_delta: +0.034052
collision_speed_proxy: 3.359023 -> 3.322625
minimum_road_margin_m: 0.899620 -> 0.949128
```

The severity regression is small and occurs even though collision speed and
road margin improved in that row. That means the next step should localize the
severity proxy components and row context before another repair execution. It
must not be treated as acceptable collateral damage, and it must not be hidden
by aggregate target-gate improvements.

## Supported Claims

M2649 supports these bounded claims:

```text
M2648 produced traceable source-only post-repair behavior evidence.
The M2648 repaired checkpoint changed behavior and stayed inside the M2648 run directory.
The admitted road-boundary and drift-recovery target gates passed in the M2648 proof smoke.
The protected axis diagnostic-only gate and actor-boundary gates passed.
The protected mitigation reference gate failed 1/8 and blocks promotion/performance interpretation.
```

## Rejected Claims

M2649 rejects these claims:

```text
M2648 proves driver performance.
M2648 may be promoted.
M2648 ranks controller families or selects a winner.
M2648 computes a success-rate verdict.
M2648 is a validation result.
M2648 is paper-level finite-window-vs-GRU or self-ID evidence.
M2648 is a current-sim or high-fidelity validation verdict.
M2648 target-gate pass overrides protected mitigation regression.
```

## Decision

Route to M2650 protected mitigation regression localization preflight.

M2650 should materialize row-level localization artifacts from M2641 baseline
behavior rows and M2648 post-repair behavior rows. It should identify whether
the protected mitigation regression is caused by severity proxy composition,
impact angle, collision speed, road-margin tradeoff, dynamics-axis effects, or
gate-calculation artifact.

M2650 must not run repair, training, reset, rollout, replay, validation, source
build, adapter probe, high-fidelity simulation, ranking, winner selection,
promotion, or success-rate verdict computation. It should route to
mitigation-preserving repair synthesis, implementation repair, artifact repair,
or stop.
