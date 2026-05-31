# M1977 Executable V2 Task-Quality Calibrated Repaired Measured Outcome Localization Implementation And Run

- status: completed
- decision: `task_quality_calibrated_repaired_measured_outcome_localization_pass_route_to_result_audit`
- result class: `task_quality_calibrated_repaired_measured_outcome_localization_pass`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_repaired_measured_outcome_localization.py`
- focused tests: `3 passed`
- summary: `runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/summary.json`
- source measured run: `runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired`
- reset/rollout/measured execution in M1977: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization.py
```

Result:

```text
3 passed
```

No-rerun localization:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_repaired_measured_outcome_localization \
  --summary runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/summary.json \
  --episode-rows runs/m1975_executable_v2_task_quality_calibrated_measured_execution_repaired/episode_rows.csv \
  --output-dir runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization \
  --target-episode-count 960 \
  --target-profile-count 12 \
  --target-source-kind-count 4 \
  --target-role-count 4 \
  --target-normalized-surface-count 3 \
  --target-sampled-label-count 4 \
  --next-blocker m1978-executable-v2-task-quality-calibrated-repaired-measured-outcome-localization-result-audit
```

Return code:

```text
0
```

## Pass Gate Result

M1977 passes as a no-rerun postprocess over M1975 artifacts:

```text
result_class: task_quality_calibrated_repaired_measured_outcome_localization_pass
source_result_class: task_quality_calibrated_measured_execution_pass
episode_count: 960 / 960
profile_count: 12 / 12
source_kind_count: 4 / 4
role_count: 4 / 4
normalized_surface_count: 3 / 3
sampled_label_count: 4 / 4
missing_schema_fields: []
outcome_counts_match_source_summary: true
all_selected_metrics_finite: true
required_aggregate_files_written: true
guardrail_violation_count: 0
```

The localizer did not interact with the environment or actor:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
profile_specific_tuning: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

Source outcome counts were reproduced exactly:

```text
success_obstacle_pass: 38
collision_failure: 150
off_track_noncollision_noncompletion: 772
```

## Localization Findings

Profile-level support remains diagnostic, not ranking evidence:

```text
L3_reset_control_corrected: 12 / 80 success, offtrack outcome rate 0.7000
L1_one_step: 11 / 80 success, offtrack outcome rate 0.7125
L3_online_gru: 9 / 80 success, offtrack outcome rate 0.6875
L0_current_masked: 6 / 80 success, offtrack outcome rate 0.7625
all L2 profiles: 0 / 80 success, offtrack outcome rate 0.8250-0.8625
```

Repair-source localization:

```text
anchor_neighborhood:
  episodes: 384
  success_count: 0
  collision_count: 0
  offtrack_outcome_count: 384

offtrack_boundary_relief:
  episodes: 96
  success_count: 0
  collision_count: 0
  offtrack_outcome_count: 96

success_stabilizer:
  episodes: 288
  success_count: 25
  collision_count: 44
  offtrack_outcome_count: 219

mitigation_isolation_check:
  episodes: 192
  success_count: 13
  collision_count: 106
  offtrack_outcome_count: 73
```

Scenario support:

```text
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 1
```

The one candidate-support slice is not comparison-ready:

```text
repair_source_kind: mitigation_isolation_check
source_role_semantics: unavoidable_mitigation
parent_feasibility_tier_id: tier_d_handling_limit_drift_required
normalized_surface_variant: steady_surface
sampled_obstacle_label: unavoidable
episode_count: 60
success_count: 5
collision_count: 55
offtrack_outcome_count: 0
success_rate: 0.0833333333
collision_rate: 0.9166666667
support_label: candidate_support
```

It is useful as a diagnostic collision-dominated mitigation slice, but it is
not suitable for controller-family ranking.

L2 diagnostic:

```text
l2_zero_success_diagnostic_row_count: 152
l2_total_success_count: 0
l2_same_slice_non_l2_success_pattern_count: 96
```

This says many same-slice contexts contain non-L2 successes while L2 remains
zero. It is still a public-panel diagnostic, not a finite-window-vs-GRU
conclusion.

Dominance counts:

```text
offtrack_dominance_row_count: 125
collision_dominance_row_count: 46
success_source_row_count: 38
```

## Supported Claims

M1977 supports:

- a calibrated repair-aware no-rerun localizer exists and passes focused tests;
- M1975 outcome counts are reproduced exactly;
- calibrated repair schema fields are preserved and checked:
  `parent_feasibility_tier_id`, `normalized_surface_variant`,
  `repair_source_kind`, `selection_quota_name`, and `base_geometry_source`;
- diagnostic aggregates are available across profile, repair source kind,
  role, tier, surface, label, base geometry, and candidate source slices;
- the repaired calibrated panel still has `0` comparison-ready slices under
  the M1977 rule.

## Unsupported Claims

Still unsupported:

- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification;
- high-fidelity validation readiness.

## Next

Next milestone:

```text
m1978-executable-v2-task-quality-calibrated-repaired-measured-outcome-localization-result-audit
```

M1978 should audit the localization result and choose between task-quality
repair, scenario redesign, support collection, or a strictly bounded comparison
design. Direct ranking remains blocked.
