# M2130 Paper-Route Outcome-Supported Decisive Comparison-Support Candidate Qualification Design

- status: completed
- decision: `comparison_support_candidate_qualification_design_admit_no_rerun_implementation`
- design artifact: `docs/m2130-paper-route-outcome-supported-decisive-comparison-support-candidate-qualification-design.md`
- reset/rollout/measured execution in M2130: `false`
- policy actions executed in M2130: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2130 designs a no-rerun qualification gate for the localized M2128 candidate
slices. The gate does not compare controller families. It decides which slices
are suitable inputs for a later controlled comparison design and which slices
remain diagnostic support only.

Input artifacts:

```text
runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/summary.json
runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/comparison_ready_candidates.csv
runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/comparison_support_candidates.csv
runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/offtrack_dominance_slices.csv
runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/collision_dominance_slices.csv
runs/m2128_paper_route_outcome_supported_decisive_comparison_support_outcome_localization/claim_boundary.csv
```

M2131 must read those artifacts only. It must not reset the environment, roll
out policies, tune profiles, rank profiles, or change actor inputs.

## Qualification Criteria

A slice can be marked `qualified_candidate` only if all of these checks pass:

```text
support_label == comparison_ready_candidate
episode_count >= 50
success_count >= 6
success_profile_count >= 3
success_source_count >= 5
collision_rate <= 0.30
offtrack_outcome_rate <= 0.70
all_selected_metrics_finite == true
```

The implementation must also compute diagnostic qualifiers:

```text
has_l3_success: profiles_with_success contains L3_online_gru or L3_reset_control_corrected
has_non_l3_success: profiles_with_success contains L0_current_masked, L1_one_step, or L2_window_50
source_diverse: success_source_count >= 8
profile_diverse: success_profile_count >= 4
low_collision_ready: collision_rate <= 0.20
offtrack_bounded: offtrack_outcome_rate <= 0.65
```

Those diagnostics support later panel design, but they are not rankings. A
slice can be qualified without all diagnostic flags if it satisfies the hard
criteria above.

## Confounding Checks

M2131 must classify why a non-qualified row is rejected:

```text
not_comparison_ready
insufficient_episode_count
insufficient_success_count
insufficient_profile_coverage
insufficient_source_coverage
collision_rate_too_high
offtrack_rate_too_high
nonfinite_metric
generated_proxy_boundary_only
```

The `generated_proxy_boundary_only` label must be applied to every row as a
claim-boundary flag, not as a failure by itself. It means the row can be used
for comparison design inside this smoke-proxy branch, but cannot support a
paper-level benchmark claim.

## Output Contract

M2131 must write:

```text
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/summary.json
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/qualified_candidates.csv
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/diagnostic_only_candidates.csv
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/rejection_reasons.csv
runs/m2131_paper_route_outcome_supported_decisive_comparison_support_candidate_qualification/claim_boundary.csv
```

Summary fields must include:

```text
result_class
source_result_class
source_comparison_ready_candidate_count
source_comparison_support_candidate_count
qualified_candidate_count
diagnostic_only_candidate_count
rejection_reason_counts
qualified_slice_kind_counts
qualified_intent_counts
qualified_target_support_tier_counts
qualified_source_kind_counts
qualified_proxy_template_counts
guardrail_violation_count
next_blocker
```

## Decision Rule

M2131 passes if:

```text
source summary result_class == comparison_support_outcome_localization_pass
source candidate counts reproduce M2128
qualified_candidate_count >= 6
qualified candidates cover at least 3 source_kind or intent/tier axes
guardrail_violation_count == 0
claim boundary keeps ranking/paper/FW-vs-GRU/self-ID claims false
```

If M2131 passes, route to candidate qualification result audit. That audit can
then decide whether to design a controlled comparison panel.

If M2131 yields fewer than `6` qualified candidates or collapses to one source
family, route to branch synthesis or scenario redesign rather than local repair.

## Claim Boundary

Supported by M2130:

```text
a concrete no-rerun qualification protocol for M2128 support slices.
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
m2131-paper-route-outcome-supported-decisive-comparison-support-candidate-qualification-implementation
```
