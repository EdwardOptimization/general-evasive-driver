# M2020 Multi-Slice Bounded Diagnostic Comparison Implementation And Run

- status: completed
- decision: `multi_slice_bounded_diagnostic_comparison_pass_route_to_result_audit`
- implementation: `src/autodrift/multi_slice_bounded_diagnostic_comparison.py`
- focused tests: `1 passed`
- compileall: `passed`
- summary: `runs/m2020_multi_slice_bounded_diagnostic_comparison/summary.json`
- admitted candidates: `runs/m2018_source_diverse_diagnostic_expansion_mining/admitted_expansion_candidates.csv`
- episode rows: `runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/episode_rows.csv`
- environment reset/rollout in M2020: `false`
- policy action execution in M2020: `false`
- measured rollout in M2020: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.multi_slice_bounded_diagnostic_comparison \
  --admitted-candidates runs/m2018_source_diverse_diagnostic_expansion_mining/admitted_expansion_candidates.csv \
  --episode-rows runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/episode_rows.csv \
  --output-dir runs/m2020_multi_slice_bounded_diagnostic_comparison \
  --next-blocker m2021-multi-slice-bounded-diagnostic-comparison-result-audit
```

## Result

```text
result_class: multi_slice_bounded_diagnostic_comparison_pass
candidate_count: 6
matched_episode_count: 216
candidate_profile_group_row_count: 24
aggregate_profile_group_row_count: 4
guardrail_violation_count: 0
```

Aggregate profile-group table:

```text
L0: 9/18 success, collision 3/18, offtrack outcome 6/18
L1: 8/18 success, collision 2/18, offtrack outcome 8/18
L2: 0/144 success, collision 27/144, offtrack outcome 117/144
L3: 22/36 success, collision 5/36, offtrack outcome 9/36
```

Candidate-level support:

```text
drift_required_recovery / tier_c_boundary_near_miss / post_friction_step / drift_required:
  matched 36, L2 0/24, non-L2 7/12

drift_required_recovery / tier_e_mitigation_only / steady_surface / drift_required:
  matched 24, L2 0/16, non-L2 5/8

stable_aeb / tier_c_boundary_near_miss / post_friction_step / aeb_feasible:
  matched 36, L2 0/24, non-L2 5/12

stable_aeb / tier_e_mitigation_only / post_friction_step / aeb_feasible:
  matched 36, L2 0/24, non-L2 3/12

stable_aes_only / tier_b_feasible_emergency / post_friction_step / aes_feasible:
  matched 60, L2 0/40, non-L2 17/20

unavoidable_mitigation / tier_b_feasible_emergency / post_friction_step / unavoidable:
  matched 24, L2 0/16, non-L2 2/8
```

## Interpretation Boundary

Allowed interpretation:

```text
The current public artifacts now contain a multi-slice bounded diagnostic
comparison over six admitted M2018 candidates. In these slices, L2 profiles
have zero successes while non-L2 groups retain successes, with the strongest
aggregate success in L3.
```

Forbidden interpretation:

```text
The result ranks controller families.
The result proves finite-window-vs-GRU.
The result is paper-level benchmark evidence.
The result proves level3 self-identification.
```

The main boundary remains:

```text
repair_source_kind_count: 1
```

M2020 broadens the singleton M2016 table across roles, tiers, surfaces, and
labels, but it still does not provide source-kind-diverse or private-holdout
evidence.

## Artifacts

```text
runs/m2020_multi_slice_bounded_diagnostic_comparison/summary.json
runs/m2020_multi_slice_bounded_diagnostic_comparison/candidate_profile_group_comparison.csv
runs/m2020_multi_slice_bounded_diagnostic_comparison/aggregate_profile_group_comparison.csv
runs/m2020_multi_slice_bounded_diagnostic_comparison/candidate_support.csv
runs/m2020_multi_slice_bounded_diagnostic_comparison/claim_boundary.csv
runs/m2020_multi_slice_bounded_diagnostic_comparison/run_state.json
```

## Validation

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_multi_slice_bounded_diagnostic_comparison.py
python -m compileall -q src tests
```

Both passed before final validation.

## Next

M2021 should audit this result before any new comparison, repair, or paper-route
claim. The audit must decide whether the multi-slice bounded diagnostic table
supports a controlled comparison design, requires source-kind/task-quality
repair, or should be synthesized as a bounded public diagnostic result.
