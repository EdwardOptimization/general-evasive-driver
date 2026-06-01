# M2218 Paper-Route Current-Sim Bounded Diagnostic Comparison Implementation

- status: completed
- decision: `current_sim_bounded_diagnostic_comparison_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2218-paper-route-current-sim-bounded-diagnostic-comparison-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_bounded_diagnostic_comparison.py`
- tests: `tests/test_paper_route_current_sim_bounded_diagnostic_comparison.py`
- run artifact: `runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/summary.json`
- reset in M2218: `false`
- measured execution in M2218: `false`
- policy action executed in M2218: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2218 implemented and ran the no-rerun bounded diagnostic comparison over the
M2215 scene-backed candidates.

```text
result_class: current_sim_bounded_diagnostic_comparison_pass
episode_row_count: 2304
scene_candidate_count: 9
diagnostic_row_count: 9
profile_matrix_row_count: 72
history_matrix_row_count: 36
profile_history_matrix_row_count: 72
ranking_admissible_count: 0
winner_selected: false
guardrail_violation_count: 0
```

Diagnostic labels:

```text
multi_profile_diagnostic_support: 9
profile_concentrated_support: 0
history_family_concentrated_support: 0
offtrack_dominated_diagnostic: 0
low_support_diagnostic: 0
mixed_diagnostic: 0
```

## Diagnostic Signal

All 9 scene-backed candidates pass the bounded `multi_profile_diagnostic_support`
rule. This means the scene-backed slices have at least two profiles with
non-trivial success support and are not purely single-profile artifacts.

The diagnostic matrices still show strong limitations:

```text
L2_window_25 is consistently strong on these public slices.
L3_online_gru and L3_reset_control have 0 success in the visible matrix rows.
explicit_finite_window contributes most of the history-family success.
```

This is useful diagnosis for current-sim profile/task behavior. It is not a
profile ranking, finite-window vs GRU verdict, paper result, or self-ID result.

## Artifacts

M2218 writes:

```text
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/summary.json
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_summary.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_profile_matrix.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_history_matrix.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_profile_history_matrix.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/diagnostic_claim_boundary.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/run_state.json
```

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_bounded_diagnostic_comparison.py
2 passed
```

Compile check:

```text
python -m compileall -q src/autodrift/paper_route_current_sim_bounded_diagnostic_comparison.py tests/test_paper_route_current_sim_bounded_diagnostic_comparison.py
pass
```

## Claim Boundary

Allowed claim:

```text
The M2215 scene-backed candidates have been converted into no-rerun diagnostic
matrices, and the current public panel contains multi-profile diagnostic support.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
checkpoint/profile promotion;
private-holdout generalization.
```

## Next Step

The support-slice-validity branch has reached the local-search guard boundary.
M2219 must therefore synthesize M2214-M2218 rather than add another ordinary
result-audit milestone. The synthesis should choose whether to write a bounded
diagnostic report, route to profile/history failure diagnosis, or stop this
current-sim comparison panel.
