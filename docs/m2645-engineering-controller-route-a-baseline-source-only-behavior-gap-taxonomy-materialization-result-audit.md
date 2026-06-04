# M2645 Engineering Controller Route A Source-Only Behavior Gap Taxonomy Materialization Result Audit

- status: completed
- decision: `accept_m2644_route_to_source_only_gap_targeted_repair_design`
- manifest: `experiments/manifests/m2645-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-result-audit.json`
- parent summary: `runs/m2644_engineering_controller_route_a_source_only_behavior_gap_taxonomy/summary.json`
- parent doc: `docs/m2644-engineering-controller-route-a-baseline-source-only-behavior-gap-taxonomy-materialization-preflight.md`
- parent synthesis: `docs/m2643-engineering-controller-route-a-baseline-source-only-fresh-generalization-panel-materialization-result-synthesis.md`
- follow-up manifest: `experiments/manifests/m2646-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-design.json`
- next: `m2646-engineering-controller-route-a-baseline-source-only-gap-targeted-repair-design`

## Audit Result

M2645 accepts M2644 as a source-only behavior-gap taxonomy materialization.
The taxonomy is admitted for repair-design planning only. It is not admitted as
ranking, promotion, validation, success-rate, driver-performance, paper,
current-sim, high-fidelity validation, or self-ID evidence.

Accepted M2644 summary:

```text
status_pass: true
result_class: engineering_controller_route_a_source_only_behavior_gap_taxonomy_preflight_pass
source_measured_behavior_row_count: 160
role_gap_row_count: 4
subject_gap_row_count: 20
dynamics_axis_gap_row_count: 8
repair_target_admission_row_count: 4
claim_boundary_row_count: 13
gate_matrix_row_count: 15
gate_matrix_pass: true
actor_contract_shape_72_action_3: true
taxonomy_labels_actor_visible: false
all_rows_diagnostic_only_no_ranking_claim: true
```

Required artifacts are present:

```text
summary.json
role_gap_rows.csv
subject_gap_rows.csv
dynamics_axis_gap_rows.csv
repair_target_admission_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
milestone doc
```

## Accepted Repair-Target Map

M2644 admits two repair-design targets for audit:

```text
road_departure_dominant_gap:
  source rows: 80
  source roles: stable_aes, stable_avoidable
  target scope: road_boundary_margin_control

drift_recovery_mixed_gap:
  source rows: 40
  source roles: drift_required_recovery
  target scope: drift_collision_recovery_tradeoff
```

M2644 also records two diagnostic/reference-only rows:

```text
mitigation_collision_saturated_reference:
  source rows: 40
  source role: unavoidable_mitigation
  disposition: reference_only, not a repair target

axis_sensitivity_not_yet_decisive:
  source rows: 160
  source roles: all four source-only roles
  disposition: diagnostic axis monitoring, not a repair target
```

This is the right claim boundary. It avoids using unavoidable mitigation rows
as an ordinary pass/fail denominator and avoids interpreting the current
source-only axis split as a robust-fault or delay/noise verdict.

## Actor Boundary

M2645 accepts the actor/action boundary:

```text
observation_shape: 72
action_shape: 3
taxonomy_labels_actor_visible: false
repair_target_labels_actor_visible: false
ranking_or_winner_field_emitted: false
```

Taxonomy labels, repair-target labels, and route decisions remain artifact
metadata only. They must not be used as actor inputs in later repair design or
training.

## Rejected Claims

M2645 rejects these interpretations:

```text
controller-family ranking
winner selection
checkpoint promotion
success-rate verdict
validation result
driver-performance claim
paper-level result
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness/result
level3 self-identification result
```

No reset, step, rollout, replay, validation, training, PPO, source build,
adapter probe, external high-fidelity simulation, ranking, winner selection,
promotion, or success-rate computation was executed in M2645.

## Decision

Route to M2646 source-only gap-targeted repair design.

M2646 should design a bounded repair objective and intervention plan using
only artifact-level taxonomy evidence. It should protect the P0 actor boundary,
keep taxonomy labels out of actor input, preserve mitigation reference rows,
and register a materialization or stop route. It must not train, rank,
promote, validate, or claim driver performance.
