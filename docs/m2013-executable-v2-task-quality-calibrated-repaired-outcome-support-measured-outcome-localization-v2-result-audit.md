# M2013 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured Outcome Localization V2 Result Audit

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_localization_v2_audit_route_to_bounded_comparison_qualification`
- branch: `paper_route_task_quality_calibrated_repaired_outcome_support_v2_localization`
- audited summary: `runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2/summary.json`
- next branch: `paper_route_bounded_comparison_candidate_qualification`
- reset/rollout/measured execution in M2013: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M2012 is complete as a no-rerun localization artifact over M2009:

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

The M2009 outcome counts are reproduced exactly:

```text
success_obstacle_pass: 40 / 960 = 4.17%
collision_failure: 265 / 960 = 27.60%
off_track_noncollision_noncompletion: 655 / 960 = 68.23%
```

M2012 did not interact with the environment or actor:

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

## Candidate Audit

M2012 found:

```text
comparison_ready_candidate_count: 1
comparison_support_candidate_count: 2
success_source_row_count: 40
offtrack_dominance_row_count: 103
collision_dominance_row_count: 59
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
success_rate: 28.33%
collision_rate: 3.33%
offtrack_outcome_rate: 68.33%
profiles_with_success: L0_current_masked; L1_one_step; L3_online_gru; L3_reset_control_corrected
```

This is actionable enough for a bounded qualification pass because it is no
longer a zero-support or collision-dominated slice. It is not yet enough for
controller-family ranking or paper-level comparison because support is still
single-slice, success is sparse, and offtrack remains dominant.

The second support candidate remains mitigation-like:

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
success_rate: 20.83%
collision_rate: 79.17%
```

It is useful for mitigation diagnostics, not ranking.

## L2 Diagnostic Audit

M2012 reports:

```text
l2_total_success_count: 0
l2_zero_success_diagnostic_row_count: 88
l2_same_slice_non_l2_success_pattern_count: 56
```

Allowed interpretation:

```text
The current public diagnostic panel contains many same-slice contexts where
non-L2 profiles succeed and L2 profiles do not.
```

Forbidden interpretation:

```text
Finite-window profiles are worse than current-response or GRU profiles.
```

The paper-route plans require a fair, pre-registered comparison before making
that claim. M2013 therefore routes to candidate qualification, not ranking.

## Claim-Boundary Artifact Audit

`claim_boundary.csv` has stale reason text that names M1977/M1975. This is a
text-only artifact problem: `summary.json`, source paths, outcome counts,
guardrail flags, and aggregate outputs correctly identify M2009/M2012.

Classification:

```text
artifact_text_stale_nonblocking_for_localization_pass
```

This should be repaired before public/paper artifact export if the localizer is
used again, but it does not invalidate the M2012 localization result.

## Route Decision

Decision:

```text
route_to_bounded_comparison_qualification
```

Rationale:

- M2012 fixed the previous zero-comparison-ready localization result by finding
  one actionable stable-AES candidate slice.
- The slice is not paper-ready, but it is strong enough to qualify or reject
  bounded comparison design using structural checks.
- Direct ranking would overclaim a single public slice.
- Another outcome-support repair before qualifying the new slice would risk
  local search without using the new evidence.
- Localizer claim-boundary wording is a cleanup issue, not the main scientific
  blocker.

Rejected routes:

```text
direct_controller_ranking:
  rejected because the localizer label is not audited paper-level support.

paper_level_comparison:
  rejected because support is sparse and offtrack dominated.

immediate_task_quality_repair:
  rejected because M2012 produced a new candidate that should be qualified
  before another repair branch.

level3_self_id_testing:
  rejected because this branch is task-quality/outcome support, not
  history-necessity evidence.
```

## M2014 Requirements

M2014 should implement and run a no-rerun bounded comparison qualification over
M2012 artifacts. It should produce structured candidate decisions with at least:

```text
candidate key
episode count
success support
collision/offtrack rates
profile groups represented
L0/L1/L2/L3 coverage
single-source risk
admitted_for_bounded_comparison
rejection reason
```

M2014 must not execute policy actions, rerun measured execution, tune profiles,
or rank controller families.
