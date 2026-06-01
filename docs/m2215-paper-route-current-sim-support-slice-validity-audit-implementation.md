# M2215 Paper-Route Current-Sim Support-Slice Validity Audit Implementation

- status: completed
- decision: `current_sim_support_slice_validity_audit_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2215-paper-route-current-sim-support-slice-validity-audit-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_support_slice_validity_audit.py`
- tests: `tests/test_paper_route_current_sim_support_slice_validity_audit.py`
- run artifact: `runs/m2215_paper_route_current_sim_support_slice_validity_audit/summary.json`
- reset in M2215: `false`
- measured execution in M2215: `false`
- policy action executed in M2215: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2215 implemented and ran the no-rerun support-slice validity audit over M2212
artifacts.

```text
result_class: current_sim_support_slice_validity_audit_pass
input_group_count: 212
episode_row_count: 2304
ranking_admissible_count: 0
guardrail_violation_count: 0
```

Validity labels:

```text
scene_backed_candidate: 9
history_family_diagnostic: 13
profile_only_candidate: 18
global_or_scene_blocker: 7
low_sample_or_unresolved: 60
invalid_for_ranking: 105
denominator_imbalanced: 0
```

## Interpretation

M2215 confirms that M2212 has real diagnostic support, but no ranking-admissible
support.

The scene-backed candidates are scene-level `candidate_support` groups, not a
controller-family comparison:

```text
T1 reactive emergency avoidance: 63 / 192 success
T2 delayed actuator response: 62 / 240 success
T3 diagnostic warmup obstacle reveal: 105 / 528 success
t5_boundary_axis_retarget: 63 / 192 success
```

The history-family diagnostic candidates show that explicit finite-window
profiles contain most of the current support:

```text
history_representation=explicit_finite_window: 311 / 1152 success
T1 x explicit_finite_window: 46 / 96 success
T2 x explicit_finite_window: 47 / 120 success
```

The profile-only candidates are intentionally kept out of ranking:

```text
profile_name=L2_window_25: 209 / 288 success
profile_name=L2_window_50: 82 / 288 success
profile_level=L2: 311 / 1152 success
```

This is evidence that the repaired current-sim panel contains a bounded
diagnostic slice. It is not evidence that finite-window beats GRU in a
paper-valid comparison, and it is not self-identification evidence.

## Artifacts

M2215 writes:

```text
runs/m2215_paper_route_current_sim_support_slice_validity_audit/summary.json
runs/m2215_paper_route_current_sim_support_slice_validity_audit/slice_validity.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/scene_backed_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/history_family_diagnostic_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/profile_only_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/denominator_imbalanced_slices.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/global_or_scene_blockers.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/claim_boundary.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/run_state.json
```

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_support_slice_validity_audit.py
2 passed
```

Compile check:

```text
python -m compileall -q src/autodrift/paper_route_current_sim_support_slice_validity_audit.py tests/test_paper_route_current_sim_support_slice_validity_audit.py
pass
```

## Claim Boundary

Allowed claim:

```text
M2212 support slices have been classified into scene-backed, history-family,
profile-only, blocker, and invalid-for-ranking categories without rerun.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
profile promotion.
```

## Next Step

M2216 should audit this result before choosing the next route. The likely
question is whether the `9` scene-backed candidates justify a bounded diagnostic
comparison design, or whether the branch should pivot to task-quality/profile
diagnostic repair.
