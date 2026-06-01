# M2136 Paper-Route Outcome-Supported Decisive Comparison-Support Controlled Panel Result Audit

- status: completed
- decision: `comparison_support_controlled_panel_audit_admit_comparison_protocol_design`
- audited artifact: `runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/summary.json`
- reset/rollout/measured execution in M2136: `false`
- policy actions executed in M2136: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Summary

M2134 is a clean no-rerun controlled-panel construction artifact:

```text
result_class: comparison_support_controlled_panel_construction_pass
source_result_class: comparison_support_candidate_qualification_pass
source_qualified_candidate_count: 15
actual_qualified_candidate_count: 15
qualified_count_matches_source: true
controlled_panel_unit_count: 6
controlled_panel_unit_threshold_pass: true
panel_source_kind_count: 6
panel_intent_count: 3
panel_duplicate_source_kind_count: 0
panel_broad_aggregate_exclusion_count: 3
excluded_qualified_candidate_count: 9
guardrail_violation_count: 0
```

The controlled panel units are:

```text
actuator_delay_collision_relief
gru_memory_discriminative_boundary
late_boundary_collision_relief
near_zero_margin_collision_relief
nominal_delay_support_boundary
profile_diversity_support
```

The excluded qualified rows are expected diagnostics:

```text
broad_aggregate_candidate: 3
duplicate_source_kind_lower_priority: 6
```

The claim boundary remains intact:

```text
controller_family_ranking: false
finite_window_vs_gru_conclusion: false
paper_level_benchmark_result: false
level3_self_identification: false
```

## Decision

M2136 admits comparison protocol design.

This does not admit ranking. The next design must define how the six panel
units can be compared without double-counting, tuning profiles, or claiming
paper-level evidence from generated smoke-proxy rows.

M2137 should define:

```text
panel-unit inclusion contract;
profile set and allowed profile labels;
per-unit metrics to compare;
minimum support and non-completion handling;
whether ranking is still blocked after protocol design;
what result artifact is needed before any comparison execution;
what audit must happen before any paper-route interpretation.
```

## Supported Claims

Supported:

```text
M2134 produced a non-overlapping six-unit controlled panel with source-count
reproduction, duplicate source-kind count 0, broad aggregate exclusion 3, and
guardrail 0.
```

Also supported:

```text
The controlled panel is sufficient to design a comparison protocol.
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
m2137-paper-route-outcome-supported-decisive-comparison-support-comparison-protocol-design
```
