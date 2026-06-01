# M2139 Paper-Route Outcome-Supported Decisive Comparison-Support Comparison Protocol Materialization Audit

- status: completed
- decision: `comparison_support_protocol_materialization_audit_admit_denominator_source_inventory_design`
- audited artifact: `runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/summary.json`
- reset/rollout/measured execution in M2139: `false`
- policy actions executed in M2139: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Summary

M2138 is a clean materialized support-matrix artifact:

```text
result_class: comparison_support_comparison_protocol_materialization_pass
source_result_class: comparison_support_controlled_panel_construction_pass
panel_unit_count: 6
profile_label_count: 4
support_matrix_row_count: 24
expected_support_matrix_row_count: 24
supported_intent_count: 3
supported_source_kind_count: 6
panel_duplicate_source_kind_count: 0
direct_broad_aggregate_panel_unit_count: 0
generated_proxy_boundary_panel_unit_count: 6
claim_boundary_violation_count: 0
guardrail_violation_count: 0
per_profile_rate_computed: false
winner_or_rank_computed: false
```

The profile support summary is:

```text
L0_current_masked: 3/6 panel units, 2 intents, 3 source kinds
L1_one_step: 5/6 panel units, 3 intents, 5 source kinds
L3_online_gru: 6/6 panel units, 3 intents, 6 source kinds
L3_reset_control_corrected: 6/6 panel units, 3 intents, 6 source kinds
```

These counts are support coverage only. They are not a performance comparison.

## Metric Boundary

M2138 correctly admits only support-coverage metrics:

```text
profile_supported_unit_count
profile_supported_intent_count
profile_supported_source_kind_count
```

M2138 correctly blocks:

```text
per_profile_success_rate
winner_or_rank
finite_window_vs_gru_verdict
paper_level_benchmark_verdict
level3_self_id_verdict
```

The blocker is structural: M2134 and M2138 do not carry per-profile denominators.
Absence from `profiles_with_success` means no observed success support in the
M2134 aggregate, not a measured profile failure rate.

## Interpretation

M2138 supports:

```text
The generated-proxy comparison-support branch has a clean six-unit support
matrix with machine-readable metric and claim boundaries.
```

M2138 does not support:

```text
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark result;
level3 self-identification.
```

The support matrix also does not separate `L3_online_gru` from
`L3_reset_control_corrected`: both have observed support on all six panel units.
That is useful as a routing signal, but it is not mechanism evidence.

## Decision

M2139 admits a denominator-source inventory design.

Reason:

```text
The support matrix is clean, but the next missing evidence is not another
coverage table. The next missing evidence is whether existing measured
artifacts can provide per-profile denominators for each panel unit and profile
label without rerun. If not, the branch must design a controlled rerun or route
to scenario redesign.
```

The next milestone should design an inventory protocol that answers:

```text
For each M2138 panel_unit_id x profile_label, can we locate a source artifact
with total episodes, success count, collision count, offtrack count, and
claim-boundary metadata?
```

It should still not rank profiles.

## Supported Claims

Supported:

```text
M2138 cleanly materialized a no-rerun support matrix over M2134 controlled
panel units.
```

Also supported:

```text
The next route should focus on denominator-source inventory, because the current
support matrix lacks per-profile denominator evidence.
```

## Unsupported Claims

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
m2140-paper-route-outcome-supported-decisive-comparison-support-denominator-source-inventory-design
```
