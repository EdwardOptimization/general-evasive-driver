# M2014 Bounded Comparison Candidate Qualification Implementation And Run

- status: completed
- decision: `bounded_comparison_candidate_qualification_pass_route_to_result_audit`
- result class: `bounded_comparison_candidate_qualification_pass`
- implementation: `src/autodrift/bounded_comparison_candidate_qualification.py`
- focused tests: `3 passed`
- compileall: `passed`
- summary: `runs/m2014_bounded_comparison_candidate_qualification/summary.json`
- source localization: `runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2`
- environment reset/rollout in M2014: `false`
- policy action execution in M2014: `false`
- measured rollout in M2014: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_bounded_comparison_candidate_qualification.py
```

Result:

```text
3 passed
```

No-rerun qualification:

```bash
PYTHONPATH=src python -m autodrift.bounded_comparison_candidate_qualification \
  --summary runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/summary.json \
  --candidates runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/comparison_support_candidates.csv \
  --output-dir runs/m2014_bounded_comparison_candidate_qualification \
  --next-blocker m2015-bounded-comparison-candidate-qualification-result-audit
```

Return code:

```text
0
```

## Qualification Rules

Default thresholds:

```text
min_episode_count: 48
min_success_count: 10
min_success_rate: 0.15
max_collision_rate: 0.10
max_offtrack_outcome_rate: 0.75
min_nonzero_success_profile_count: 3
min_success_profile_group_count: 2
```

These rules do not rank controller families. They only decide whether a
localizer-labeled candidate is admissible for a bounded diagnostic comparison
design.

## Result

M2014 passes:

```text
result_class: bounded_comparison_candidate_qualification_pass
source_candidate_count: 2
qualification_row_count: 2
admitted_candidate_count: 1
rejected_candidate_count: 1
guardrail_violation_count: 0
```

The admitted candidate is:

```text
candidate_key:
  success_stabilizer|stable_aes_only|tier_b_feasible_emergency|post_friction_step|aes_feasible

episode_count: 60
success_count: 17
collision_count: 2
offtrack_outcome_count: 41
success_rate: 0.2833333333
collision_rate: 0.0333333333
offtrack_outcome_rate: 0.6833333333
success_profile_groups: L0;L1;L3
l2_success_present: false
l2_total_success_count: 0
admitted_scope: bounded_diagnostic_comparison_not_finite_window_vs_gru
```

The rejected candidate is:

```text
candidate_key:
  success_stabilizer|drift_required_recovery|tier_e_mitigation_only|steady_surface|drift_required

rejection_reasons:
  source_label_not_comparison_ready_candidate
  episode_count_below_threshold
  success_count_below_threshold
  collision_rate_above_threshold
```

## Interpretation Boundary

M2014 supports a bounded diagnostic-comparison route for the admitted stable-AES
slice. It does not support:

- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark evidence;
- policy improvement;
- level3 self-identification.

Because `l2_success_present=false` and `l2_total_success_count=0`, any next
comparison design must explicitly treat L2 as zero-success on this public slice
and must not generalize that into a finite-window verdict.

## Next

Next milestone:

```text
m2015-bounded-comparison-candidate-qualification-result-audit
```

M2015 should audit whether the admitted bounded diagnostic comparison scope is
useful enough to design a small controlled comparison or whether task-quality
repair/scenario redesign is still required.
