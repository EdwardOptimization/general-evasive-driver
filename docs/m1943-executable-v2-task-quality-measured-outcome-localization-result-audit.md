# M1943 Executable V2 Task-Quality Measured Outcome Localization Result Audit

- status: completed
- decision: `task_quality_measured_outcome_localization_audit_route_to_offtrack_support_repair`
- branch: `paper_route_task_quality_measured_outcome_localization`
- audited summary: `runs/m1942_executable_v2_task_quality_measured_outcome_localization/summary.json`
- next branch: `paper_route_task_quality_offtrack_support_repair`
- reset/rollout/measured execution in M1943: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M1942 is complete as a no-rerun localization artifact.

Pass-gate fields:

```text
result_class: task_quality_measured_outcome_localization_pass
source_result_class: task_quality_measured_execution_pass
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

Localizer guardrails are clean:

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

## Outcome Support Audit

M1942 reproduced the M1938 outcome counts exactly:

```text
success_obstacle_pass: 40 / 960 = 4.17%
collision_failure: 105 / 960 = 10.94%
off_track_noncollision_noncompletion: 815 / 960 = 84.90%
```

This confirms the current blocker:

```text
outcome_support_low_offtrack_dominated
```

It is not a runner failure, source-count mismatch, metric artifact, contract
violation, private-holdout leak, or profile-tuning issue.

## Comparison Readiness

M1942 found:

```text
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 2
```

The two candidate-support slices are:

```text
tier_c_boundary_near_miss / stable_aeb / post_friction_step / aeb_feasible
tier_c_boundary_near_miss / stable_aeb / steady_surface / aeb_feasible
```

Both have:

```text
episode_count: 24
success_count: 5
collision_count: 1
offtrack_outcome_count: 18
success_rate: 20.83%
collision_rate: 4.17%
offtrack_outcome_rate: 75.00%
```

They are useful support-collection anchors, but they are not comparison-ready
under the M1941 rule because off-track rate remains above `0.70`.

Therefore:

```text
controller-family ranking remains blocked
bounded comparison design remains premature
```

## L2 Diagnostic Audit

M1942 found:

```text
l2_zero_success_diagnostic_row_count: 320
l2_total_success_count: 0
l2_same_slice_non_l2_success_pattern_count: 136
```

This is a strong diagnostic signal that the L2 profiles are mismatched to the
current panel. But it is not yet a controller-family conclusion, because the
panel remains off-track dominated and has no comparison-ready slice.

Allowed interpretation:

```text
The current public diagnostic panel contains many same-slice contexts where
non-L2 profiles succeed and L2 profiles do not.
```

Forbidden interpretation:

```text
Finite-window profiles are worse than current-response or GRU profiles.
```

That claim requires a pre-registered comparison run on support-sufficient
scenarios.

## Route Decision

Decision:

```text
route_to_offtrack_support_repair
```

Rationale:

- no comparison-ready slice exists;
- two candidate-support slices show nonzero success and same-slice profile
  diversity;
- the dominant failure mode is off-track noncollision noncompletion;
- collision is not the main blocker for those candidate-support slices;
- the correct next step is to repair or collect support around off-track
  dominated task geometry before ranking.

Rejected routes:

```text
comparison_design:
  rejected because comparison_ready_candidate_count == 0.

scenario_redesign_from_scratch:
  rejected for now because candidate-support slices exist.

direct_controller_ranking:
  rejected because support is low and off-track dominated.

level3_self_id_testing:
  rejected because this branch is task-quality/scenario support, not
  history-necessity evidence.
```

## M1944 Requirements

M1944 should design the next branch:

```text
paper_route_task_quality_offtrack_support_repair
```

It should not run a new rollout. It should define:

- which M1942 slices are used as positive support anchors;
- how off-track dominance will be reduced without tuning profiles;
- whether repair is by scenario geometry, termination semantics, support
  collection, or source resampling;
- what pass gates are required before any new measured execution;
- how L2 diagnostic rows are kept as diagnostics, not ranking evidence.

## Supported Claims

M1943 supports:

- M1942 localization is complete and guardrail-clean;
- M1938/M1942 are not comparison-ready;
- off-track support repair is the correct next branch;
- L2 zero-success is a diagnostic route-finding signal only.

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
m1944-executable-v2-task-quality-offtrack-support-repair-design
```

M1944 should design the off-track support repair branch before any new
materialization or measured execution.
