# M2012 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured Outcome Localization V2

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2_pass_route_to_result_audit`
- result class: `task_quality_calibrated_repaired_measured_outcome_localization_pass`
- source measured run: `runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat`
- summary: `runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/summary.json`
- environment reset/rollout in M2012: `false`
- policy action execution in M2012: `false`
- measured rollout in M2012: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_repaired_measured_outcome_localization \
  --summary runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/summary.json \
  --episode-rows runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/episode_rows.csv \
  --output-dir runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2 \
  --target-episode-count 960 \
  --target-profile-count 12 \
  --target-source-kind-count 4 \
  --target-role-count 4 \
  --target-normalized-surface-count 3 \
  --target-sampled-label-count 4 \
  --next-blocker m2013-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-outcome-localization-v2-result-audit
```

Return code:

```text
0
```

## Pass Gate Result

M2012 passes as a no-rerun postprocess over M2009 artifacts:

```text
result_class: task_quality_calibrated_repaired_measured_outcome_localization_pass
source_result_class: task_quality_calibrated_measured_execution_pass
episode_count: 960 / 960
profile_count: 12 / 12
source_kind_count: 4 / 4
role_count: 4 / 4
normalized_surface_count: 3 / 3
sampled_label_count: 4 / 4
outcome_counts_match_source_summary: true
all_selected_metrics_finite: true
required_aggregate_files_written: true
guardrail_violation_count: 0
```

No environment or actor execution occurred:

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

M2012 reproduces the M2009 source outcomes:

```text
success_obstacle_pass: 40
collision_failure: 265
off_track_noncollision_noncompletion: 655
```

## Localization Findings

The localizer found:

```text
comparison_ready_candidate_count: 1
comparison_support_candidate_count: 2
success_source_row_count: 40
offtrack_dominance_row_count: 103
collision_dominance_row_count: 59
l2_total_success_count: 0
l2_zero_success_diagnostic_row_count: 88
l2_same_slice_non_l2_success_pattern_count: 56
```

The localizer-labeled comparison-ready candidate is:

```text
repair_source_kind: success_stabilizer
source_role_semantics: stable_aes_only
parent_feasibility_tier_id: tier_b_feasible_emergency
normalized_surface_variant: post_friction_step
sampled_obstacle_label: aes_feasible
episode_count: 60
success_count: 17
collision_count: 2
offtrack_outcome_count: 41
success_rate: 0.2833333333
collision_rate: 0.0333333333
offtrack_outcome_rate: 0.6833333333
profiles_with_success: L0_current_masked;L1_one_step;L3_online_gru;L3_reset_control_corrected
```

The second support candidate is mitigation-like, not ranking-ready:

```text
repair_source_kind: success_stabilizer
source_role_semantics: drift_required_recovery
parent_feasibility_tier_id: tier_e_mitigation_only
normalized_surface_variant: steady_surface
sampled_obstacle_label: drift_required
episode_count: 24
success_count: 5
collision_count: 19
offtrack_outcome_count: 0
success_rate: 0.2083333333
collision_rate: 0.7916666667
profiles_with_success: L0_current_masked;L1_one_step;L3_online_gru;L3_reset_control_corrected
```

Profile-level outcomes remain diagnostic only:

```text
L3_online_gru: 11 / 80 success
L3_reset_control_corrected: 11 / 80 success
L0_current_masked: 9 / 80 success
L1_one_step: 9 / 80 success
all L2 profiles: 0 / 80 success
```

This is not a finite-window vs GRU conclusion; it is a public diagnostic
pattern requiring a later controlled comparison if M2013 admits that route.

## Artifact Caveat

`claim_boundary.csv` contains stale wording that refers to M1977/M1975. The
summary paths, source outcome counts, guardrail flags, and aggregate artifacts
correctly point to M2009/M2012. M2013 must audit whether this text-only artifact
should be repaired before comparison-design work.

## Supported Claims

M2012 supports:

- the no-rerun localizer runs cleanly on M2009 artifacts;
- M2009 outcome counts are reproduced exactly;
- aggregate outcome diagnostics exist across profile, source kind, role, tier,
  surface, label, base geometry, and candidate-source slices;
- at least one localizer-labeled comparison-ready slice now exists and must be
  audited before any ranking route.

## Unsupported Claims

Still unsupported:

- controller-family ranking;
- paper-level benchmark result;
- finite-window vs GRU conclusion;
- policy improvement;
- level3 self-identification;
- high-fidelity validation readiness.

## Next

Next milestone:

```text
m2013-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-outcome-localization-v2-result-audit
```

M2013 should audit the localizer-labeled comparison-ready slice, the stale
claim-boundary wording, and the remaining low-support/offtrack dominance before
choosing comparison design, targeted repair, or scenario redesign.
