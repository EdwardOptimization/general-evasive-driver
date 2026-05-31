# M1978 Executable V2 Task-Quality Calibrated Repaired Measured Outcome Localization Result Audit

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_localization_audit_route_to_outcome_support_repair`
- branch: `paper_route_task_quality_calibrated_repaired_outcome_localization`
- audited summary: `runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/summary.json`
- next branch: `paper_route_task_quality_calibrated_repaired_outcome_support_repair`
- reset/rollout/measured execution in M1978: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Completeness Audit

M1977 is complete as a no-rerun calibrated repair-aware localization artifact.

Pass-gate fields:

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

M1977 reproduced the M1975 outcome counts exactly:

```text
success_obstacle_pass: 38 / 960 = 3.96%
collision_failure: 150 / 960 = 15.63%
off_track_noncollision_noncompletion: 772 / 960 = 80.42%
```

## Comparison Readiness

M1977 found:

```text
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 1
```

The single candidate-support slice is:

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
success_rate: 8.33%
collision_rate: 91.67%
offtrack_outcome_rate: 0.00%
profiles_with_success: L1_one_step; L3_online_gru; L3_reset_control_corrected
```

This is useful as a mitigation/collision diagnostic. It is not
comparison-ready because collision dominates the slice.

Therefore:

```text
controller-family ranking remains blocked
bounded comparison design remains premature
```

## Outcome Support Audit

The current blocker is not metadata, runner completeness, metric completeness,
actor input, training, replay, PPO, or a private-holdout issue. The blocker is
task/outcome support quality:

```text
outcome_support_low_offtrack_and_collision_dominated
```

Two distinct support problems are now visible.

First, large offtrack-only blocks:

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
```

Second, collision-dominated mitigation blocks:

```text
mitigation_isolation_check:
  episodes: 192
  success_count: 13
  collision_count: 106
  offtrack_outcome_count: 73

mitigation_isolation_check / unavoidable_mitigation / steady_surface:
  episodes: 60
  success_count: 5
  collision_count: 55
  offtrack_outcome_count: 0
```

Success support is concentrated in non-L2 and mostly in repaired support
families:

```text
success_stabilizer: 25 successes
mitigation_isolation_check: 13 successes
anchor_neighborhood: 0 successes
offtrack_boundary_relief: 0 successes
```

## L2 Diagnostic Audit

M1977 found:

```text
l2_zero_success_diagnostic_row_count: 152
l2_total_success_count: 0
l2_same_slice_non_l2_success_pattern_count: 96
```

Allowed interpretation:

```text
The current public diagnostic panel contains many calibrated-repaired
same-slice contexts where non-L2 profiles succeed and L2 profiles do not.
```

Forbidden interpretation:

```text
Finite-window profiles are worse than current-response or GRU profiles.
```

That claim still requires a support-sufficient, pre-registered comparison run.

## Route Decision

Decision:

```text
route_to_outcome_support_repair
```

Rationale:

- no comparison-ready slice exists;
- the one candidate-support slice is collision-dominated;
- offtrack dominance is still broad and includes large zero-success slices;
- outcome support problems are localized enough to repair before a full
  scenario redesign;
- direct ranking would overfit to sparse public diagnostic support.

Rejected routes:

```text
comparison_design:
  rejected because comparison_ready_candidate_count == 0.

direct_controller_ranking:
  rejected because support is sparse and offtrack/collision dominated.

scenario_redesign_from_scratch:
  rejected for now because support concentration is localized enough to design
  a bounded repair branch first.

level3_self_id_testing:
  rejected because this branch is task-quality/outcome support, not
  history-necessity evidence.
```

## M1979 Requirements

M1979 should design the next branch:

```text
paper_route_task_quality_calibrated_repaired_outcome_support_repair
```

It should not run a new rollout. It should define:

- offtrack-only support repair for `anchor_neighborhood` and
  `offtrack_boundary_relief`;
- collision-aware mitigation repair for the `mitigation_isolation_check`
  unavoidable slices;
- how to preserve M1975/M1977 as baseline diagnostic evidence;
- which no-rollout template/source-mining artifacts are required before reset;
- pass gates that require nonzero comparison-ready support before any ranking.

## Supported Claims

M1978 supports:

- M1977 localization is complete and guardrail-clean;
- M1975/M1977 are not comparison-ready;
- the next branch should repair outcome support rather than rank controllers;
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
m1979-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-design
```

M1979 should design the outcome-support repair branch before any new
materialization, reset validation, or measured execution.
