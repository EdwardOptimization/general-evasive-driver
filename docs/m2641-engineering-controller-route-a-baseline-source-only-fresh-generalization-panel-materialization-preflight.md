# M2641 Engineering Controller Route A Source-Only Fresh Generalization Panel Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_fresh_generalization_panel_preflight_pass`
- manifest: `experiments/manifests/m2641-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_route_a_source_only_fresh_generalization_panel.py`
- summary: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/summary.json`
- seed panel spec: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/seed_panel_spec.csv`
- subject registry: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/subject_registry.csv`
- dynamics axis rows: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/dynamics_axis_rows.csv`
- actor visibility guard rows: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/actor_visibility_guard_rows.csv`
- telemetry rows: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/telemetry_rows.csv`
- measured behavior rows: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_behavior_rows.csv`
- measured event rows: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/measured_event_rows.csv`
- metric completeness rows: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/metric_completeness_rows.csv`
- gate matrix: `runs/m2641_engineering_controller_route_a_source_only_fresh_generalization_panel/gate_matrix.csv`
- next milestone: `m2642-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-audit`
- external high-fidelity simulation/source build/adapter probe/replay/training: `false`
- ranking/winner selection/promotion/success-rate/performance verdicts: `false`
- paper/FW-vs-GRU/current-sim/high-fidelity/self-ID claims: `false`

## Materialized Panel

M2641 executes bounded source-only policy and open-loop reference
rollouts over four Route A role families, four fresh seeds per
role, and two diagnostic dynamics axes. The actor contract remains
P0 human-view 72 observations and 3 deployed action dimensions.

Accepted summary:

```text
status_pass: true
role_family_count: 4
fresh_seed_count_per_role: 4
dynamics_axis_count: 2
comparison_subject_count: 5
measured_behavior_row_count: 160
measured_event_row_count: 160
telemetry_row_count: 12800
actor_contract_shape_72_action_3: true
actor_visibility_guard_rows_pass: true
gate_matrix_pass: true
delay_noise_diagnostic_metadata_only: true
```

## Claim Boundary

The `fresh_fault_delay_noise` axis applies source-only fault scales
through the local four-wheel backend. Actuator delay and sensor
noise fields are diagnostic metadata and actor-visibility guard
targets in M2641; they are not actor inputs and are not claimed as
external high-fidelity validation physics.

M2641 is a source-only diagnostic materialization. It does not rank
subjects, compute a success-rate verdict, select a winner, promote a
checkpoint, validate a controller, or claim driver performance.

## Next Route

Route to:

```text
m2642-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-audit
```

The next audit should accept or reject these materialized rows before
any ranking, repair, promotion, validation, or performance claim.
