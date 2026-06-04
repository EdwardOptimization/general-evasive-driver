# M2664 Engineering Controller Route A Protected Mitigation Fresh Panel Failure Taxonomy Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy_preflight_pass`
- manifest: `experiments/manifests/m2664-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-preflight.json`
- route plan: `docs/post-m2470-route-plan.md`
- implementation: `src/autodrift/engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy.py`
- summary: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/summary.json`
- subject taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/subject_failure_taxonomy_rows.csv`
- axis taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/axis_failure_taxonomy_rows.csv`
- metric taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/metric_failure_taxonomy_rows.csv`
- combined taxonomy rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/combined_failure_taxonomy_rows.csv`
- claim boundary rows: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/claim_boundary_rows.csv`
- gate matrix: `runs/m2664_engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy/gate_matrix.csv`
- next milestone: `m2665-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-result-audit`
- reset/step/rollout/replay/validation/training/PPO executed: `false`
- ranking/winner/promotion/success-rate/performance claims: `false`

## Materialized Taxonomy

M2664 reanalyzes the accepted M2662 fresh protected mitigation panel
into subject, axis, metric, and subject-axis failure taxonomy rows. The
taxonomy is artifact metadata only and is not actor-visible.

Accepted summary:

```text
status_pass: true
m2662_panel_spec_row_count: 12
m2662_measured_behavior_row_count: 60
m2662_protected_gate_row_count: 27
fresh_protected_seed_count: 4
fresh_protected_seed_ids: 268200,268201,268202,268203
subject_failure_taxonomy_row_count: 3
axis_failure_taxonomy_row_count: 3
metric_failure_taxonomy_row_count: 3
combined_failure_taxonomy_row_count: 9
protected_gate_blocking_row_count: 25
protected_gate_regressed_row_count: 79
gate_matrix_pass: true
```

## Boundary

The protected mitigation rows remain outside success denominators. M2664
does not rank controller families, select a winner, promote a checkpoint,
compute success rate, validate a controller, or claim driver performance,
paper-level evidence, finite-window-vs-GRU result, current-sim verdict,
high-fidelity validation, full ideal driver completion, or self-ID.

Route to:

```text
m2665-engineering-controller-route-a-protected-mitigation-fresh-panel-failure-taxonomy-materialization-result-audit
```
