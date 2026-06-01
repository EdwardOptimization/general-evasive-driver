# M2143 Paper-Route Outcome-Supported Decisive Comparison-Support Denominator-Backed Comparison Protocol Design

- status: completed
- decision: `denominator_backed_comparison_protocol_design_admit_materialization`
- design artifact: `docs/m2143-paper-route-outcome-supported-decisive-comparison-support-denominator-backed-comparison-protocol-design.md`
- reset/rollout/measured execution in M2143: `false`
- policy actions executed in M2143: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2143 designs a no-rerun denominator-backed diagnostic comparison artifact from
M2141 denominator rows.

The protocol may compute descriptive rates and pre-registered diagnostic deltas.
It must not produce a profile ranking, winner, family-superiority verdict,
finite-window-vs-GRU conclusion, paper-level result, or self-ID claim.

## Inputs

M2144 should read:

```text
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/summary.json
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/denominator_inventory_rows.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/profile_denominator_summary.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/source_kind_denominator_summary.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/metric_contract.csv
runs/m2141_paper_route_outcome_supported_decisive_comparison_support_denominator_source_inventory/claim_boundary.csv
```

It must not reset the environment, roll out policies, execute policy actions,
train, replay, run PPO, tune profiles, or change actor inputs.

## Included Profiles and Panel Units

Include all measured profiles:

```text
L0_current_masked
L1_one_step
L2_window_50
L3_online_gru
L3_reset_control_corrected
```

Include all six source kinds:

```text
actuator_delay_collision_relief
gru_memory_discriminative_boundary
late_boundary_collision_relief
near_zero_margin_collision_relief
nominal_delay_support_boundary
profile_diversity_support
```

Reject materialization if any profile or source kind is missing.

## Descriptive Metrics

M2144 may compute per-profile and per-source-kind descriptive metrics:

```text
episode_count
success_count
collision_count
offtrack_outcome_count
success_rate = success_count / episode_count
collision_rate = collision_count / episode_count
offtrack_outcome_rate = offtrack_outcome_count / episode_count
clearance_margin_mean_unweighted
return_mean_unweighted
steps_mean_unweighted
observed_success_support_count
```

These metrics are descriptive diagnostics over generated-proxy rows.

## Diagnostic Contrasts

M2144 may compute these pre-registered pairwise deltas:

```text
L1_one_step - L0_current_masked
L2_window_50 - L1_one_step
L3_online_gru - L1_one_step
L3_online_gru - L2_window_50
L3_reset_control_corrected - L3_online_gru
L3_reset_control_corrected - L2_window_50
```

For each contrast, compute:

```text
success_rate_delta
collision_rate_delta
offtrack_outcome_rate_delta
clearance_margin_mean_delta
return_mean_delta
```

Every contrast row must include:

```text
contrast_scope: diagnostic_generated_proxy_only
verdict_allowed: false
ranking_allowed: false
paper_claim_allowed: false
self_id_claim_allowed: false
```

The contrast rows are evidence for audit routing only. They are not a verdict.

## Blocked Fields

M2144 output is invalid if it contains any of these fields:

```text
rank
winner
best_profile
beats
outperforms
family_superiority
finite_window_vs_gru_verdict
gru_advantage_claim
self_identification_claim
paper_level_benchmark_result
```

Allowed language:

```text
descriptive_rate
diagnostic_delta
generated_proxy_boundary
claim_blocked
audit_required_before_interpretation
```

## Output Contract

M2144 should write:

```text
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/summary.json
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/comparison_protocol.json
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/profile_outcome_summary.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/source_kind_profile_matrix.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/diagnostic_contrast_rows.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/metric_contract.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/claim_boundary.csv
runs/m2144_paper_route_outcome_supported_decisive_comparison_support_denominator_backed_comparison/run_state.json
```

Summary fields should include:

```text
result_class
source_result_class
profile_count
source_kind_count
denominator_row_count
profile_summary_row_count
source_kind_profile_matrix_row_count
diagnostic_contrast_row_count
blocked_verdict_field_count
claim_boundary_violation_count
guardrail_violation_count
ranking_claim_made
winner_selected
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
next_blocker
```

## Decision Rule

M2144 passes if:

```text
source result_class == comparison_support_denominator_source_inventory_pass
profile_count == 5
source_kind_count == 6
denominator_row_count == 30
profile_summary_row_count == 5
source_kind_profile_matrix_row_count == 30
diagnostic_contrast_row_count == 6
blocked_verdict_field_count == 0
claim_boundary_violation_count == 0
guardrail_violation_count == 0
ranking_claim_made == false
winner_selected == false
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If M2144 passes, route to a result audit. The audit may describe what the
diagnostic rates and deltas show, but it still must not issue a ranking or
paper-level verdict.

## Supported Claims

Supported by M2143:

```text
a bounded no-rerun protocol for denominator-backed descriptive diagnostics over
the M2141 inventory.
```

Unsupported:

```text
controller-family ranking;
winner selection;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

Next milestone:

```text
m2144-paper-route-outcome-supported-decisive-comparison-support-denominator-backed-comparison-materialization
```
