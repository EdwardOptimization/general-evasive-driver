# M2133 Paper-Route Outcome-Supported Decisive Comparison-Support Controlled Panel Design

- status: completed
- decision: `comparison_support_controlled_panel_design_admit_no_rerun_construction`
- design artifact: `docs/m2133-paper-route-outcome-supported-decisive-comparison-support-controlled-panel-design.md`
- reset/rollout/measured execution in M2133: `false`
- policy actions executed in M2133: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2133 designs a no-rerun controlled panel construction step from M2131
qualified candidates. The goal is to avoid double-counting broad aggregate
rows and paired source-kind rows before any controller-family comparison.

Input artifacts:

```text
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/summary.json
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/qualified_candidates.csv
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/diagnostic_only_candidates.csv
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/rejection_reasons.csv
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/claim_boundary.csv
```

M2134 must read those artifacts only. It must not reset the environment, roll
out policies, execute policy actions, train, tune profiles, or rank profiles.

## Panel Unit Rules

The primary panel unit is a nonempty `source_kind` slice.

Eligible primary candidates:

```text
qualification_label == qualified_candidate
support_label == comparison_ready_candidate
source_kind is nonempty
slice_kind in {outcome_by_intent_source_kind, outcome_by_source_kind}
```

Canonical selection per `source_kind`:

```text
prefer outcome_by_intent_source_kind over outcome_by_source_kind;
break ties by higher success_count;
then lower collision_rate;
then lower offtrack_outcome_rate;
then lexical candidate_key.
```

This yields one panel unit per `source_kind` and prevents duplicate evidence
from the paired `outcome_by_intent_source_kind` and `outcome_by_source_kind`
rows.

Diagnostic-only qualified rows:

```text
outcome_by_proxy_template
outcome_by_intent
outcome_by_target_support_tier
non-selected duplicate source_kind rows
```

Those rows can describe panel context, but they are not direct comparison
units.

## Expected M2131-Derived Panel

M2134 should construct a primary panel with these six source kinds:

```text
actuator_delay_collision_relief
gru_memory_discriminative_boundary
late_boundary_collision_relief
near_zero_margin_collision_relief
nominal_delay_support_boundary
profile_diversity_support
```

The expected primary panel size is therefore `6` rows. The remaining `9`
qualified rows should be diagnostic/excluded because they are broad aggregates
or duplicate source-kind views.

## Output Contract

M2134 must write:

```text
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/summary.json
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/controlled_panel_units.csv
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/excluded_qualified_candidates.csv
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/panel_diagnostics.csv
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/claim_boundary.csv
```

Summary fields must include:

```text
result_class
source_result_class
source_qualified_candidate_count
controlled_panel_unit_count
excluded_qualified_candidate_count
panel_source_kind_count
panel_intent_count
panel_duplicate_source_kind_count
panel_broad_aggregate_exclusion_count
guardrail_violation_count
next_blocker
```

## Decision Rule

M2134 passes if:

```text
source result_class == comparison_support_candidate_qualification_pass
source_qualified_candidate_count == 15
controlled_panel_unit_count >= 6
panel_source_kind_count >= 6
panel_duplicate_source_kind_count == 0
panel_broad_aggregate_exclusion_count >= 3
guardrail_violation_count == 0
claim boundary keeps ranking/paper/FW-vs-GRU/self-ID claims false
```

If M2134 passes, route to result audit. The audit may then decide whether a
controlled comparison protocol can be designed.

If M2134 cannot produce at least six non-overlapping source-kind panel units,
route to branch synthesis or scenario redesign rather than ranking aggregates.

## Claim Boundary

Supported by M2133:

```text
a concrete no-rerun panel construction protocol for M2131 qualified candidates.
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
m2134-paper-route-outcome-supported-decisive-comparison-support-controlled-panel-construction
```
