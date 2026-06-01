# M2137 Paper-Route Outcome-Supported Decisive Comparison-Support Comparison Protocol Design

- status: completed
- decision: `comparison_support_protocol_design_admit_no_rerun_materialization`
- design artifact: `docs/m2137-paper-route-outcome-supported-decisive-comparison-support-comparison-protocol-design.md`
- reset/rollout/measured execution in M2137: `false`
- policy actions executed in M2137: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2137 designs a no-rerun protocol for converting the M2134 controlled panel
into a bounded comparison-support matrix.

The protocol is not a ranking experiment. It can answer:

```text
Which controller-profile labels have observed success support on which
non-overlapping generated-proxy panel units?
```

It cannot answer:

```text
Which controller family is best?
Does finite-window beat GRU or GRU beat finite-window?
Is the result paper-level benchmark evidence?
Is level3 self-identification proven?
```

## Input Contract

M2138 must read only these M2134 artifacts:

```text
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/summary.json
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/controlled_panel_units.csv
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/excluded_qualified_candidates.csv
runs/m2134_paper_route_outcome_supported_decisive_comparison_support_controlled_panel/claim_boundary.csv
```

It must not reset the environment, roll out policies, execute policy actions,
train, tune profiles, run replay, run PPO, or change actor inputs.

## Panel Unit Inclusion

Include every row in `controlled_panel_units.csv` that satisfies:

```text
panel_role == primary_source_kind_unit
qualification_label == qualified_candidate
support_label == comparison_ready_candidate
source_kind is nonempty
generated_proxy_boundary_only == true
```

Reject the protocol materialization if:

```text
controlled_panel_unit_count < 6
panel_source_kind_count < 6
panel_duplicate_source_kind_count != 0
guardrail_violation_count != 0
any broad aggregate row enters direct panel units
```

The expected panel units remain:

```text
actuator_delay_collision_relief
gru_memory_discriminative_boundary
late_boundary_collision_relief
near_zero_margin_collision_relief
nominal_delay_support_boundary
profile_diversity_support
```

The excluded qualified rows are diagnostic only. They can be counted in the
summary, but they must not become comparison units.

## Profile Label Contract

The profile universe is the union of semicolon-separated labels in
`profiles_with_success` across included panel units.

For the current M2134 panel, the expected labels are:

```text
L0_current_masked
L1_one_step
L3_online_gru
L3_reset_control_corrected
```

These labels are observed support labels, not tuned contenders. M2138 must not
rename them into controller-family winners or collapse them into finite-window
vs GRU conclusions.

If a profile label is absent from a unit's `profiles_with_success`, encode:

```text
observed_success_support: false
absence_semantics: no_success_support_observed_in_m2134_aggregate
```

Do not encode absence as a measured failure rate, because M2134 does not carry
per-profile denominators.

## Metric Contract

M2138 may compute panel-unit metrics copied from M2134:

```text
episode_count
success_count
collision_count
offtrack_outcome_count
success_rate
collision_rate
offtrack_outcome_rate
success_profile_count
success_source_count
comparison_support_intent
source_kind
```

M2138 may compute support-matrix metrics:

```text
profile_supported_unit_count
profile_supported_unit_fraction
profile_supported_intent_count
profile_supported_source_kind_count
profile_collision_relief_support_count
profile_discriminative_boundary_support_count
profile_support_ladder_medium_support_count
profile_generated_proxy_boundary_only
```

M2138 must not compute:

```text
per-profile success_rate
per-profile collision_rate
per-profile offtrack_rate
mean return
winner
rank
finite-window-vs-GRU verdict
paper_validity verdict
level3 self-ID verdict
```

Reason: M2134 contains outcome support aggregates, not a controlled per-profile
denominator table.

## Non-Completion Handling

The materialization result must use explicit status values:

```text
materialization_pass
materialization_blocked_missing_input
materialization_blocked_panel_contract_violation
materialization_blocked_claim_boundary_violation
materialization_blocked_metric_contract_violation
```

If the result is blocked, M2138 should write a summary and claim boundary file
with the blocking reason, then route to synthesis or scenario redesign. It
should not patch the panel by adding broad aggregates or duplicate source-kind
rows.

## Ranking Blockers

Ranking remains blocked after M2137.

M2138 output is invalid if it contains:

```text
best_profile
winner
rank
outperforms
beats
finite_window_better_than_gru
gru_better_than_finite_window
paper_level_benchmark_result
level3_self_identification
```

Allowed language is limited to support coverage, observed support, missing
support, and protocol materialization status.

## M2138 Output Contract

M2138 should materialize:

```text
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/summary.json
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/comparison_protocol.json
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/panel_units_normalized.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/profile_support_matrix.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/profile_support_summary.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/metric_contract.csv
runs/m2138_paper_route_outcome_supported_decisive_comparison_support_comparison_protocol/claim_boundary.csv
```

Summary fields should include:

```text
result_class
source_result_class
panel_unit_count
profile_label_count
support_matrix_row_count
supported_intent_count
supported_source_kind_count
guardrail_violation_count
ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
next_blocker
```

## Decision Rule

M2138 passes if:

```text
source result_class == comparison_support_controlled_panel_construction_pass
panel_unit_count == 6
profile_label_count >= 3
support_matrix_row_count == panel_unit_count * profile_label_count
supported_source_kind_count == 6
guardrail_violation_count == 0
claim boundary keeps ranking/paper/FW-vs-GRU/self-ID claims false
```

If M2138 passes, route to a protocol materialization audit. The audit may decide
whether the support matrix is sufficient to design a later controlled comparison
execution, but it still must not interpret the support matrix as ranking.

If M2138 cannot materialize a support matrix without violating the contract,
route to synthesis or scenario redesign.

## Supported Claims

Supported by M2137:

```text
a concrete no-rerun support-matrix protocol for M2134 controlled panel units.
```

Also supported:

```text
M2138 can materialize comparison-support artifacts without executing policies,
provided it preserves the no-ranking and generated-proxy claim boundary.
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
m2138-paper-route-outcome-supported-decisive-comparison-support-comparison-protocol-materialization
```
