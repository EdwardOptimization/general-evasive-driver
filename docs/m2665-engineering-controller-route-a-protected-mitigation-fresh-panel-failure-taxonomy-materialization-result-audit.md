# M2665 Engineering Controller Route A Protected Mitigation Fresh Panel Failure Taxonomy Materialization Result Audit

- status: completed
- decision: `accept_m2664_route_to_protected_mitigation_fresh_panel_taxonomy_branch_synthesis`
- manifest: `experiments/manifests/m2665-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-result-audit.json`
- route plan: `docs/post-m2470-route-plan.md`
- parent summary: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/summary.json`
- parent subject taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/subject_failure_taxonomy_rows.csv`
- parent axis taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/axis_failure_taxonomy_rows.csv`
- parent metric taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/metric_failure_taxonomy_rows.csv`
- parent combined taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/combined_failure_taxonomy_rows.csv`
- parent claim boundary rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/claim_boundary_rows.csv`
- parent gate matrix: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2666-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-branch-synthesis.json`
- next: `m2666-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-branch-synthesis`

## Audit Result

M2665 accepts M2664 as a valid Route A protected mitigation fresh-panel
failure-taxonomy materialization. The result is accepted as blocker-structure
evidence only. It is not repair success, controller ranking, checkpoint
promotion, success-rate, validation, driver-performance, paper,
finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver,
or self-ID evidence.

Accepted M2664 summary:

```text
status_pass: true
required_artifacts_present: true
source_artifacts_present: true
m2662_status_pass: true
m2662_panel_spec_row_count: 12
m2662_measured_behavior_row_count: 60
m2662_protected_gate_row_count: 27
fresh_protected_seed_count: 4
subject_failure_taxonomy_row_count: 3
axis_failure_taxonomy_row_count: 3
metric_failure_taxonomy_row_count: 3
combined_failure_taxonomy_row_count: 9
claim_boundary_row_count: 16
gate_matrix_row_count: 37
gate_matrix_pass: true
protected_gate_blocking_row_count: 25
protected_gate_regressed_row_count: 79
all_policy_subjects_blocking: true
all_axes_blocking: true
all_metrics_blocking: true
broad_protected_blocker_preserved: true
target_protected_split_preserved: true
protected_rows_in_success_denominator: false
actor_contract_shape_72_action_3: true
hidden_oracle_actor_input_detected: false
taxonomy_labels_actor_visible: false
```

## Failure Taxonomy Audit

Subject taxonomy:

```text
m1154_original_policy: 9/9 blocking, 27 regressed row counts, saturated blocker
m2532_guarded_repair_policy: 8/9 blocking, 26 regressed row counts, mixed blocker
m2537_mitigation_preserving_policy: 8/9 blocking, 26 regressed row counts, mixed blocker
```

Axis taxonomy:

```text
fresh_protected_close_cut_in_fault: 9/9 blocking, 34 regressed row counts, saturated blocker
fresh_protected_fault_delay_noise: 9/9 blocking, 23 regressed row counts, saturated blocker
fresh_protected_nominal: 7/9 blocking, 22 regressed row counts, mixed blocker
```

Metric taxonomy:

```text
minimum_obstacle_clearance_m: 9/9 blocking, 28 regressed row counts, saturated blocker
obstacle_penetration_proxy_m: 9/9 blocking, 28 regressed row counts, saturated blocker
severity_proxy: 7/9 blocking, 23 regressed row counts, mixed blocker
```

This is a broad protected mitigation blocker. It is not isolated to one
checkpoint, one dynamics axis, one metric, or one original public row.

## Claim Boundary Audit

M2664 claim-boundary and gate-matrix rows pass. The only supported operational
claims are:

```text
M2664 materialized the protected mitigation fresh-panel failure taxonomy.
M2664 preserved protected blocker semantics.
M2664 registered a follow-up result audit.
```

M2664 correctly rejects:

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
full_ideal_driver_completion
```

## Actor Boundary

M2665 accepts the actor/action boundary:

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: false
taxonomy_labels_actor_visible: false
protected_rows_in_success_denominator: false
```

M2664 taxonomy labels, blocker labels, route decisions, and gate outcomes are
artifact metadata only. They must not become actor inputs.

## Decision

Route to M2666 branch synthesis.

The reason is operational: M2662-M2665 have now materialized, audited,
taxonomized, and audited the protected mitigation fresh-panel blocker. The
next aligned action is a synthesis decision that decides stop, pivot, or a new
evidence route. Opening another same-row repair loop from this taxonomy would
carry high public-gate/local-search risk.

M2666 must not run reset, step, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner selection,
promotion, or success-rate computation.

No repair-success, driver-performance, validation, paper-level,
finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver,
or self-ID claim is made.
