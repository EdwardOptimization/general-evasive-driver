# M2663 Engineering Controller Route A Protected Mitigation Fresh Failure-Surface Panel Materialization Result Audit

- status: completed
- decision: `accept_m2662_route_to_protected_mitigation_fresh_panel_failure_taxonomy`
- manifest: `experiments/manifests/m2663-engineering-controller-route-a-protected-mitigation-fresh-failure-surface-panel-materialization-result-audit.json`
- route plan: `docs/post-m2470-route-plan.md`
- parent summary: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/summary.json`
- parent panel spec: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/panel_spec_rows.csv`
- parent measured behavior rows: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/measured_behavior_rows.csv`
- parent protected gates: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/protected_mitigation_gate_rows.csv`
- parent claim boundary rows: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/claim_boundary_rows.csv`
- parent gate matrix: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2664-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-preflight.json`
- next: `m2664-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-preflight`

## Audit Result

M2663 accepts M2662 as a fresh Route A protected mitigation failure-surface
panel materialization. The panel is accepted as protected-blocker evidence and
fresh-panel diagnostic data only. It is not admitted as repair success,
checkpoint promotion, validation, ranking, success-rate, driver-performance,
paper, current-sim, high-fidelity validation, finite-window-vs-GRU, full ideal
driver, or self-ID evidence.

This follows `docs/post-m2470-route-plan.md`: Route A is treated as the
engineering-controller mainline with bounded failure taxonomy and contract
hygiene, while paper/self-ID and current-sim verdict claims remain separate.

Accepted M2662 summary:

```text
status_pass: true
panel_spec_row_count: 12
measured_behavior_row_count: 60
protected_mitigation_gate_row_count: 27
claim_boundary_row_count: 15
gate_matrix_row_count: 24
fresh_protected_seed_count: 4
dynamics_axis_count: 3
fresh_failure_surface_axis_count: 8
protected_gate_blocking_row_count: 25
protected_gate_regressed_row_count: 79
target_protected_split_preserved: true
protected_blocker_source_preserved: true
actor_contract_shape_72_action_3: true
hidden_oracle_actor_input_detected: false
ranking_run: false
winner_selected: false
checkpoint_promoted: false
success_rate_computed: false
driver_performance_claim_made: false
```

Required artifacts are present:

```text
summary.json
panel_spec_rows.csv
measured_behavior_rows.csv
protected_mitigation_gate_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
milestone doc
```

## Evidence Audit

M2662 expands the protected mitigation evidence axis beyond the M2657-M2660
same-row index and audit loop:

```text
fresh protected seeds: 268200, 268201, 268202, 268203
source focus seeds: 267100, 267101, 267102, 267103
dynamics axes:
  fresh_protected_nominal
  fresh_protected_fault_delay_noise
  fresh_protected_close_cut_in_fault
comparison subjects:
  m1154_original_policy
  m2532_guarded_repair_policy
  m2537_mitigation_preserving_policy
  coast_open_loop
  straight_full_brake_open_loop
```

Protected gate distribution:

```text
gate rows: 27
gate pass: 2
gate fail: 25
blocking rows: 25
regressed protected row count: 79

blocking by subject:
  m1154_original_policy: 9
  m2532_guarded_repair_policy: 8
  m2537_mitigation_preserving_policy: 8

blocking by axis:
  fresh_protected_close_cut_in_fault: 9
  fresh_protected_fault_delay_noise: 9
  fresh_protected_nominal: 7

blocking by metric:
  severity_proxy: 7
  obstacle_penetration_proxy_m: 9
  minimum_obstacle_clearance_m: 9
```

This confirms that the blocker is not limited to the original M2650/M2657 row.
The fresh panel turns the protected mitigation issue into a broader failure
surface that should be taxonomized before any repair or objective change.

## Claim Boundary Audit

M2662 claim-boundary rows pass. The allowed claims are only:

```text
fresh protected mitigation source-only panel materialized
fresh protected seeds and fresh failure-surface axes materialized
protected mitigation remains blocking and outside success denominators
```

M2662 correctly rejects:

```text
repair_success
controller_family_ranking
winner_selection
checkpoint_promotion
success_rate_verdict
driver_performance
validation_result
high_fidelity_validation_result
paper_level_evidence
finite_window_vs_gru
current_sim_verdict
level3_self_identification
```

## Actor Boundary

M2663 accepts the actor/action boundary:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
localization_labels_actor_visible: false
objective_gate_labels_actor_visible: false
route_decision_labels_actor_visible: false
```

Protected-panel seeds, dynamics axes, panel specs, gate outcomes, and route
decisions are artifact metadata only. They must not become actor inputs.

## Supported Claims

M2663 supports these bounded claims:

```text
M2662 materialized a fresh protected mitigation failure-surface panel.
The panel used fresh protected seeds and a fresh close-cut-in fault axis.
The panel preserved P0 72/action 3 and no hidden/oracle actor inputs.
Protected mitigation failure remains blocking.
Protected rows remain outside target success denominators.
The M2662 panel is ready for failure-taxonomy materialization.
```

## Rejected Claims

M2663 rejects these interpretations:

```text
M2662 proves repair success.
M2662 ranks controller families or selects a winner.
M2662 promotes any checkpoint.
M2662 computes a success-rate verdict.
M2662 is validation, driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver, or self-ID evidence.
The protected blocker can be weakened or hidden inside aggregate success.
Another same-row public repair loop is admitted before taxonomy.
```

## Decision

Route to M2664 protected mitigation fresh-panel failure taxonomy
materialization.

M2664 should consume M2662 artifacts only:

```text
summary.json
panel_spec_rows.csv
measured_behavior_rows.csv
protected_mitigation_gate_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
```

M2664 should materialize subject/axis/metric failure taxonomy rows and a claim
boundary for the fresh protected panel. It must not run reset, step, rollout,
replay, validation, training, PPO, source build, adapter probe, external
simulation, ranking, winner selection, promotion, or success-rate computation.

No repair-success, driver-performance, validation, paper-level,
finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver,
or self-ID claim is made.
