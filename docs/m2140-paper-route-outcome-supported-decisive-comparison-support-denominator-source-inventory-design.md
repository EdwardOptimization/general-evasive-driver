# M2140 Paper-Route Outcome-Supported Decisive Comparison-Support Denominator-Source Inventory Design

- status: completed
- decision: `denominator_source_inventory_design_admit_no_rerun_materialization`
- design artifact: `docs/m2140-paper-route-outcome-supported-decisive-comparison-support-denominator-source-inventory-design.md`
- reset/rollout/measured execution in M2140: `false`
- policy actions executed in M2140: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2140 designs a no-rerun denominator-source inventory for the M2138 panel.

M2138 provides support coverage, not rates. M2140 therefore asks a narrower
question before any comparison:

```text
For every M2138 panel source_kind and every measured profile label, can existing
artifacts provide a denominator row with episode_count, success_count,
collision_count, offtrack count, finite metrics, and claim-boundary metadata?
```

This is still not a ranking experiment.

## Input Artifacts

M2141 should read:

```text
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/summary.json
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/panel_units_normalized.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/profile_support_matrix.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/claim_boundary.csv
runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/outcome_by_profile_source_kind.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/summary.json
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/profile_aggregate.csv
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/claim_boundary.csv
```

Optional fallback input:

```text
runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/episode_rows.csv
```

The fallback is only for denominator reconstruction if the aggregate inventory
is missing rows. It is not a new rollout.

## Profile Universe

Do not use only the M2138 `profiles_with_success` union as the comparison
profile universe. That union excludes profiles with zero observed support and
therefore cannot represent denominator evidence.

M2141 should use the measured profile universe from M2125:

```text
L0_current_masked
L1_one_step
L2_window_50
L3_online_gru
L3_reset_control_corrected
```

Expected inventory size:

```text
6 panel source_kinds * 5 measured profiles = 30 denominator rows
```

## Matching Rule

For each row in `panel_units_normalized.csv`:

```text
panel_unit_id
source_kind
comparison_support_intent
```

and each measured profile label from M2125, find exactly one row in:

```text
outcome_by_profile_source_kind.csv
```

where:

```text
profile_name == measured profile label
source_kind == panel source_kind
slice_kind == outcome_by_profile_source_kind
```

The inventory row should copy:

```text
episode_count
success_count
collision_count
offtrack_outcome_count
success_rate
collision_rate
offtrack_outcome_rate
clearance_margin_mean
return_mean
steps_mean
all_selected_metrics_finite
success_obstacle_pass
collision_failure
off_track_noncollision_noncompletion
termination_off_track
termination_obstacle_collision
termination_empty
```

It should also join the M2138 support flag when present:

```text
observed_success_support
support_absence_semantics
```

For profiles absent from the M2138 support matrix, such as `L2_window_50`,
encode:

```text
observed_success_support: false
support_absence_semantics: profile_not_in_m2138_success_support_union
```

## Availability Labels

Each inventory row must have one of these labels:

```text
denominator_available_from_profile_source_kind_aggregate
missing_profile_source_kind_denominator
duplicate_profile_source_kind_denominator
nonfinite_denominator_metrics
claim_boundary_blocked
```

M2141 passes only if all 30 expected rows are
`denominator_available_from_profile_source_kind_aggregate`.

## Output Contract

M2141 should write:

```text
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/summary.json
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/denominator_inventory_rows.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/profile_denominator_summary.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/source_kind_denominator_summary.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/metric_contract.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/claim_boundary.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/run_state.json
```

Summary fields should include:

```text
result_class
source_result_class
panel_unit_count
measured_profile_count
expected_denominator_row_count
denominator_inventory_row_count
available_denominator_row_count
missing_denominator_row_count
duplicate_denominator_row_count
nonfinite_denominator_row_count
claim_boundary_violation_count
guardrail_violation_count
ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
next_blocker
```

## Metric Contract

M2141 may inventory denominator-backed metrics:

```text
episode_count
success_count
collision_count
offtrack_outcome_count
success_rate
collision_rate
offtrack_outcome_rate
clearance_margin_mean
return_mean
steps_mean
```

M2141 must not compute:

```text
winner
rank
family superiority
finite-window-vs-GRU verdict
paper-level verdict
level3 self-ID verdict
```

Denominator inventory makes later comparison possible. It does not perform that
comparison.

## Decision Rule

M2141 passes if:

```text
M2125 result_class == comparison_support_measured_execution_pass
M2138 result_class == comparison_support_comparison_protocol_materialization_pass
panel_unit_count == 6
measured_profile_count == 5
expected_denominator_row_count == 30
denominator_inventory_row_count == 30
available_denominator_row_count == 30
missing_denominator_row_count == 0
duplicate_denominator_row_count == 0
nonfinite_denominator_row_count == 0
claim_boundary_violation_count == 0
guardrail_violation_count == 0
```

If it passes, route to denominator inventory result audit. The audit can decide
whether to design a denominator-backed controlled comparison. It still cannot
rank profiles.

If it fails because no-rerun denominator evidence is unavailable, route to a
controlled rerun design or synthesis.

## Supported Claims

Supported by M2140:

```text
a concrete no-rerun denominator-source inventory protocol for M2138 panel units
and the complete M2125 measured profile universe.
```

Unsupported:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

Next milestone:

```text
m2141-paper-route-outcome-supported-decisive-comparison-support-denominator-source-inventory-materialization
```
