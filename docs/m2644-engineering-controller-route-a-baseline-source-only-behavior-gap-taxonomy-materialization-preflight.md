# M2644 Engineering Controller Route A Source-Only Behavior Gap Taxonomy Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_source_only_behavior_gap_taxonomy_preflight_pass`
- manifest: `experiments/manifests/m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-preflight.json`
- implementation: `src/autodrift/engineering_controller_route_a_source_only_behavior_gap_taxonomy.py`
- summary: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/summary.json`
- role gap rows: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/role_gap_rows.csv`
- subject gap rows: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/subject_gap_rows.csv`
- dynamics axis gap rows: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/dynamics_axis_gap_rows.csv`
- repair target admission rows: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/repair_target_admission_rows.csv`
- claim boundary rows: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/claim_boundary_rows.csv`
- gate matrix: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/gate_matrix.csv`
- next milestone: `m2645-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-result-audit`
- reset/step/rollout/replay/validation/training/PPO executed: `false`
- ranking/winner/promotion/success-rate/performance claims: `false`

## Materialized Taxonomy

M2644 reanalyzes the accepted M2641 measured behavior rows into
role, subject, dynamics-axis, repair-target, claim-boundary, and
gate rows. Taxonomy labels and repair-target labels are artifact
metadata only and are not actor-visible inputs.

Accepted summary:

```text
status_pass: true
source_measured_behavior_row_count: 160
role_gap_row_count: 4
subject_gap_row_count: 20
dynamics_axis_gap_row_count: 8
repair_target_admission_row_count: 4
claim_boundary_row_count: 13
gate_matrix_pass: true
road_departure_dominant_gap_present: true
drift_recovery_mixed_gap_present: true
mitigation_collision_saturated_reference_present: true
axis_sensitivity_not_yet_decisive_present: true
```

## Result

M2644 creates a source-only repair-target map for audit. It does
not rank subjects, select a winner, promote checkpoints, compute
success rates, validate a controller, or claim driver performance.

Route to:

```text
m2645-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-result-audit
```
