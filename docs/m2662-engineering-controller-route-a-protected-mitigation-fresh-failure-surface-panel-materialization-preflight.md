# M2662 Route A Protected Mitigation Fresh Failure-Surface Panel

- status: completed
- result_class: `engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel_materialization_preflight_pass`
- manifest: `experiments/manifests/m2662-engineering-controller-route-a-protected-mitigation-fresh-failure-surface-panel-materialization-preflight.json`
- summary: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/summary.json`
- panel spec rows: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/panel_spec_rows.csv`
- measured behavior rows: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/measured_behavior_rows.csv`
- protected mitigation gate rows: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/protected_mitigation_gate_rows.csv`
- claim boundary rows: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/claim_boundary_rows.csv`
- gate matrix: `runs/m2662_engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2663-engineering-controller-route-a-protected-mitigation-fresh-failure-surface-panel-materialization-result-audit.json`
- next: `m2663-engineering-controller-route-a-protected-mitigation-fresh-failure-surface-panel-materialization-result-audit`

## Materialized Evidence

```text
protected_role: unavoidable_mitigation
fresh_protected_seed_count: 4
dynamics_axis_count: 3
panel_spec_row_count: 12
measured_behavior_row_count: 60
protected_mitigation_gate_row_count: 27
protected_gate_blocking_row_count: 25
actor_contract_shape_72_action_3: True
hidden_oracle_actor_input_detected: False
gate_matrix_pass: True
```

M2662 consumes M2657-M2661 target/protected evidence as design input only,
then runs a fresh source-only protected mitigation panel over new protected
seeds and three dynamics axes. Protected rows remain outside target success
denominators.

## Protected Gate Summary

- `m2662_m1154_original_policy_fresh_protected_close_cut_in_fault_severity_proxy_against_reference`: gate_pass=False regressed=4
- `m2662_m1154_original_policy_fresh_protected_close_cut_in_fault_obstacle_penetration_against_reference`: gate_pass=False regressed=3
- `m2662_m1154_original_policy_fresh_protected_close_cut_in_fault_minimum_obstacle_clearance_against_reference`: gate_pass=False regressed=3
- `m2662_m1154_original_policy_fresh_protected_fault_delay_noise_severity_proxy_against_reference`: gate_pass=False regressed=3
- `m2662_m1154_original_policy_fresh_protected_fault_delay_noise_obstacle_penetration_against_reference`: gate_pass=False regressed=2
- `m2662_m1154_original_policy_fresh_protected_fault_delay_noise_minimum_obstacle_clearance_against_reference`: gate_pass=False regressed=2
- `m2662_m1154_original_policy_fresh_protected_nominal_severity_proxy_against_reference`: gate_pass=False regressed=4
- `m2662_m1154_original_policy_fresh_protected_nominal_obstacle_penetration_against_reference`: gate_pass=False regressed=3
- `m2662_m1154_original_policy_fresh_protected_nominal_minimum_obstacle_clearance_against_reference`: gate_pass=False regressed=3
- `m2662_m2532_guarded_repair_policy_fresh_protected_close_cut_in_fault_severity_proxy_against_reference`: gate_pass=False regressed=4
- `m2662_m2532_guarded_repair_policy_fresh_protected_close_cut_in_fault_obstacle_penetration_against_reference`: gate_pass=False regressed=4
- `m2662_m2532_guarded_repair_policy_fresh_protected_close_cut_in_fault_minimum_obstacle_clearance_against_reference`: gate_pass=False regressed=4
- `m2662_m2532_guarded_repair_policy_fresh_protected_fault_delay_noise_severity_proxy_against_reference`: gate_pass=False regressed=2
- `m2662_m2532_guarded_repair_policy_fresh_protected_fault_delay_noise_obstacle_penetration_against_reference`: gate_pass=False regressed=3
- `m2662_m2532_guarded_repair_policy_fresh_protected_fault_delay_noise_minimum_obstacle_clearance_against_reference`: gate_pass=False regressed=3
- `m2662_m2532_guarded_repair_policy_fresh_protected_nominal_severity_proxy_against_reference`: gate_pass=True regressed=0
- `m2662_m2532_guarded_repair_policy_fresh_protected_nominal_obstacle_penetration_against_reference`: gate_pass=False regressed=3
- `m2662_m2532_guarded_repair_policy_fresh_protected_nominal_minimum_obstacle_clearance_against_reference`: gate_pass=False regressed=3

## Claim Boundary

- blocking protected gate rows: 25
- supported operational claim: fresh protected mitigation failure-surface panel materialized
- rejected claims: repair success, driver performance, controller ranking, winner selection, checkpoint promotion, success-rate verdict, validation result, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation result, full ideal driver completion, or self-ID evidence

## Gate Matrix

- `source_artifacts_present`: True
- `follow_up_manifest_registered`: True
- `fresh_protected_seeds`: True
- `protected_role_only`: True
- `dynamics_axis_count`: True
- `fresh_failure_surface_axis_present`: True
- `panel_spec_row_count`: True
- `measured_behavior_row_count`: True
- `telemetry_row_count`: True
- `reset_count`: True
- `target_protected_split_preserved`: True
- `protected_blocker_source_preserved`: True
- `actor_contract_shape_72_action_3`: True
- `hidden_oracle_actor_input_detected`: True
- `all_policy_checkpoints_admitted`: True
- `all_actions_finite`: True
- `all_actions_within_bounds`: True
- `all_rows_diagnostic_only`: True
- `claim_boundary_rows_pass`: True
- `ranking_run`: True
- `winner_selected`: True
- `checkpoint_promoted`: True
- `success_rate_computed`: True
- `driver_performance_claim_made`: True
