# M2134 Paper-Route Outcome-Supported Decisive Comparison-Support Controlled Panel Construction

- status: completed
- decision: `comparison_support_controlled_panel_construction_pass_route_to_result_audit`
- run artifact: `runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/summary.json`
- focused tests: `3 passed`
- reset/rollout/measured execution in M2134: `false`
- policy actions executed in M2134: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation Summary

M2134 adds a no-rerun controlled panel constructor:

```text
src/autodrift/paper_route_outcome_supported_decisive_comparison_support_controlled_panel.py
tests/test_paper_route_outcome_supported_decisive_comparison_support_controlled_panel.py
```

The constructor reads M2131 qualification artifacts only. It constructs one
canonical panel unit per nonempty `source_kind`, preferring
`outcome_by_intent_source_kind` over the duplicate `outcome_by_source_kind`
view. Broad aggregate candidates remain diagnostic and are not direct panel
units.

## Command

Executed:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_controlled_panel \
  --summary runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/summary.json \
  --qualified-candidates runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/qualified_candidates.csv \
  --claim-boundary runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/claim_boundary.csv \
  --output-dir runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel \
  --min-panel-units 6 \
  --next-blocker m2135-paper-route-outcome-supported-decisive-comparison-support-branch-synthesis
```

## Result

M2134 passes no-rerun controlled panel construction:

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

Panel source kinds:

```text
actuator_delay_collision_relief
gru_memory_discriminative_boundary
late_boundary_collision_relief
near_zero_margin_collision_relief
nominal_delay_support_boundary
profile_diversity_support
```

Excluded qualified candidates:

```text
broad_aggregate_candidate: 3
duplicate_source_kind_lower_priority: 6
```

## Claim Boundary

Supported:

```text
M2134 materialized a non-overlapping six-unit controlled panel from M2131
qualified candidates without rerun and with guardrail 0.
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
m2135-paper-route-outcome-supported-decisive-comparison-support-branch-synthesis
```
