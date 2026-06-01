# M2219 Paper-Route Current-Sim Bounded Diagnostic Comparison Branch Synthesis

- status: completed
- decision: `current_sim_bounded_diagnostic_comparison_synthesis_pivot_to_profile_history_failure_diagnosis`
- synthesis decision: `pivot`
- synthesis window: `M2214-M2218`
- primary failure taxonomy: `scenario_sampling_failure`
- reset in M2219: `false`
- measured execution in M2219: `false`
- policy action executed in M2219: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2214 froze a no-rerun validity audit that separates M2212 support slices into:

```text
scene_backed_candidate
history_family_diagnostic
profile_only_candidate
denominator_imbalanced
global_or_scene_blocker
low_sample_or_unresolved
invalid_for_ranking
```

M2215 implemented that audit:

```text
result_class: current_sim_support_slice_validity_audit_pass
input_group_count: 212
scene_backed_candidate: 9
history_family_diagnostic: 13
profile_only_candidate: 18
global_or_scene_blocker: 7
ranking_admissible_count: 0
guardrail_violation_count: 0
```

M2216 correctly admitted only a bounded diagnostic comparison design, not a
ranking route.

M2217 froze a no-rerun bounded diagnostic comparison over scene-backed
candidates only, with:

```text
diagnostic_only: true
ranking_admissible: false
winner_selected: false
```

M2218 implemented the diagnostic matrices:

```text
result_class: current_sim_bounded_diagnostic_comparison_pass
scene_candidate_count: 9
multi_profile_diagnostic_support_count: 9
profile_concentrated_support_count: 0
history_family_concentrated_support_count: 0
profile_matrix_row_count: 72
history_matrix_row_count: 36
profile_history_matrix_row_count: 72
ranking_admissible_count: 0
winner_selected: false
guardrail_violation_count: 0
```

The most important diagnostic pattern is:

```text
L2_window_25 has strong success on the public scene-backed candidates.
L3_online_gru and L3_reset_control have zero success in the visible matrix rows.
explicit_finite_window contributes most history-family successes.
```

## Supported Claims

Supported:

```text
1. The project can now produce claim-safe no-rerun diagnostic matrices from
   public current-sim outcome artifacts.
2. The current public panel contains scene-backed multi-profile diagnostic
   support.
3. The same public panel shows a serious recurrent-profile failure signal:
   L3_online_gru and L3_reset_control are zero-success on the visible
   scene-backed matrix rows.
4. M2218 keeps ranking, winner selection, paper claims, finite-window-vs-GRU
   claims, and self-ID claims blocked.
```

## Falsified Claims

Falsified or still unsupported:

```text
The current public panel is ready for controller-family ranking.
M2218 proves finite-window beats GRU.
M2218 provides paper-level benchmark evidence.
M2218 provides level3 self-identification evidence.
The next useful action is another blind offtrack-support repair.
```

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  The broad panel remains too public and too offtrack-heavy for ranking.

none:
  M2214-M2218 harness/code paths passed their guardrails and did not run new
  rollout or policy actions.
```

The active blocker has changed. It is no longer whether support slices can be
localized. It is why the recurrent profiles are zero-success on the bounded
diagnostic slices and whether that reflects training/checkpoint weakness,
profile configuration, task bias, or a meaningful finite-window advantage.

## Public-Gate Overfit Risk

Risk is high if the project reports M2218 as a result table:

```text
The slices are public and derived from repeated repair/localization work.
The global panel remains offtrack dominated.
The diagnostic matrices show strong L2 support but zero L3 support.
No private holdout, rerun, history intervention, or training-seed repeat is
being used here.
```

The safe use is diagnostic: use the matrices to decide what to inspect next.

## Actual Capability Change

The branch changed project capability from:

```text
localized support/blocker rows
```

to:

```text
claim-safe diagnostic matrices over scene-backed public support slices
```

That is enough to diagnose profile/history failures. It is not enough to rank
controllers or write a paper result.

## Next Branch Decision

Selected:

```text
pivot:
  paper_route_current_sim_profile_history_failure_diagnosis
```

The next branch should design a no-rerun metric audit over the M2209 episode
rows and M2218 matrices, focused on the L3 zero-success signal and the L2
finite-window success signal. It should ask:

```text
1. Are L3 failures early offtrack, collision, slow noncompletion, or recovery
   failures?
2. Do L3_online_gru and L3_reset_control fail identically?
3. Is L2_window_25 success associated with lower action-rate, later offtrack,
   different drift usage, or better clearance?
4. Is the current profile set misconfigured, undertrained, or simply mismatched
   to the public panel?
```

Rejected routes:

```text
direct controller-family ranking;
direct finite-window vs GRU verdict;
direct paper-level claim;
direct self-ID claim;
another broad task repair before profile/history failure diagnosis;
high-fidelity simulator migration before current-sim profile failure is understood.
```

## Next

Next milestone:

```text
m2220-paper-route-current-sim-profile-history-failure-diagnosis-design
```
