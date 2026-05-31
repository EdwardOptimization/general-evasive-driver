# M1942 Executable V2 Task-Quality Measured Outcome Localization Implementation And Run

- status: completed
- decision: `task_quality_measured_outcome_localization_pass_route_to_result_audit`
- result class: `task_quality_measured_outcome_localization_pass`
- implementation: `src/autodrift/executable_v2_task_quality_measured_outcome_localization.py`
- focused tests: `2 passed`
- summary: `runs/m1942_executable_v2_task_quality_measured_outcome_localization/summary.json`
- source measured run: `runs/m1938_executable_v2_task_quality_measured_execution`
- reset/rollout/measured execution in M1942: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_measured_outcome_localization \
  --summary runs/m1938_executable_v2_task_quality_measured_execution/summary.json \
  --episode-rows runs/m1938_executable_v2_task_quality_measured_execution/episode_rows.csv \
  --output-dir runs/m1942_executable_v2_task_quality_measured_outcome_localization \
  --target-episode-count 960 \
  --target-profile-count 12 \
  --target-tier-count 5 \
  --target-role-count 4 \
  --target-surface-count 2 \
  --next-blocker m1943-executable-v2-task-quality-measured-outcome-localization-result-audit
```

Return code:

```text
0
```

## Pass Gate Result

M1942 passes as a no-rerun postprocess over existing M1938 artifacts:

```text
episode_count: 960 / 960
profile_count: 12 / 12
tier_count: 5 / 5
role_count: 4 / 4
surface_count: 2 / 2
all_selected_metrics_finite: true
outcome_counts_match_source_summary: true
required_aggregate_files_written: true
guardrail_violation_count: 0
```

Source outcome counts were reproduced exactly:

```text
success_obstacle_pass: 40
collision_failure: 105
off_track_noncollision_noncompletion: 815
```

No localizer rerun or actor interaction occurred:

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

## Localization Findings

Profile-level support remains diagnostic, not ranking evidence:

```text
L1_one_step: 12 / 80 success, offtrack outcome rate 0.7375
L0_current_masked: 10 / 80 success, offtrack outcome rate 0.7500
L3_online_gru: 9 / 80 success, offtrack outcome rate 0.7500
L3_reset_control_corrected: 9 / 80 success, offtrack outcome rate 0.7500
all L2 profiles: 0 / 80 success, offtrack outcome rate 0.8875-0.9125
```

Scenario-support localization:

```text
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 2
```

The two candidate-support slices are both `tier_c_boundary_near_miss`,
`stable_aeb`, `aeb_feasible`; one is `post_friction_step` and one is
`steady_surface`. Each has `5 / 24` success and `0.75` offtrack outcome rate.
They are not comparison-ready under the M1941 rule because offtrack remains
above the `0.70` threshold.

L2 zero-success diagnostic:

```text
l2_zero_success_diagnostic_row_count: 320
l2_total_success_count: 0
l2_same_slice_non_l2_success_pattern_count: 136
```

This means many same-slice contexts show non-L2 success while L2 remains zero,
but it is still a diagnostic public-panel pattern. It does not by itself prove
finite-window profiles are worse, because the panel is still off-track
dominated and not comparison-ready.

Dominance localization:

```text
offtrack_dominance_row_count: 170
collision_dominance_row_count: 27
success_source_row_count: 40
```

The dominant blocker remains task/scenario outcome support, especially
off-track noncollision noncompletion.

## Supported Claims

M1942 supports:

- a no-rerun outcome localizer exists and passes focused tests;
- M1938 source counts are reproduced exactly;
- diagnostic aggregates are available across profile, tier, role, surface,
  label, and source slices;
- the public panel has no comparison-ready slice under the M1941 rule;
- the L2 zero-success pattern is localized but not yet interpretable as a
  controller-family conclusion.

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
m1943-executable-v2-task-quality-measured-outcome-localization-result-audit
```

M1943 should audit this localization result and choose between task-quality
repair, support collection, scenario redesign, or a strictly bounded
comparison design. Direct ranking remains blocked.
