# M1941 Executable V2 Task-Quality Measured Outcome Localization Design

- status: completed
- decision: `task_quality_measured_outcome_localization_design_admit_implementation_and_run`
- branch: `paper_route_task_quality_measured_outcome_localization`
- source measured run: `runs/m1938_executable_v2_task_quality_measured_execution`
- no-rerun localization in M1941: `false`
- reset/rollout/measured execution in M1941: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1938 produced a complete 960-row public diagnostic measured execution, but
M1939/M1940 blocked direct controller ranking because the panel is
low-support and off-track-dominated:

```text
success_obstacle_pass: 40 / 960
collision_failure: 105 / 960
off_track_noncollision_noncompletion: 815 / 960
```

M1941 does not rerun anything. It designs a bounded localization pass over the
existing M1938 artifacts so the next step can answer:

- where the 40 successes are concentrated;
- where off-track dominance comes from;
- whether all-zero L2 profile success is profile-specific or scenario-specific;
- whether any joint slice has enough support for a later comparison;
- whether the correct next branch is task-quality repair, measured comparison
  design, or scenario redesign.

## Inputs

M1942 should read only existing M1938 artifacts:

```text
runs/m1938_executable_v2_task_quality_measured_execution/summary.json
runs/m1938_executable_v2_task_quality_measured_execution/episode_rows.csv
runs/m1938_executable_v2_task_quality_measured_execution/profile_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/tier_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/role_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/surface_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/sampled_label_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/outcome_aggregate.csv
runs/m1938_executable_v2_task_quality_measured_execution/termination_reason_aggregate.csv
```

M1942 must not call environment reset or rollout code. It is a CSV/JSON
postprocess over already measured public diagnostic data.

## Localization Slices

The localizer should produce aggregates over these primary dimensions:

```text
profile_name
feasibility_tier_id
source_role_semantics
surface_variant
sampled_obstacle_label
target_boundary_mode
target_support_mode
selected_accepted_cell_rule
source_split
candidate_source_id
task_source_id
outcome_bucket
termination_reason
```

Required joint slices:

```text
profile x outcome
profile x termination_reason
tier x outcome
role x outcome
surface x outcome
sampled_label x outcome
profile x tier x outcome
profile x role x outcome
profile x surface x outcome
profile x sampled_label x outcome
tier x role x surface x outcome
candidate_source x profile x outcome
```

The implementation should also write focused diagnostic tables:

```text
success_source_rows.csv
offtrack_dominance_rows.csv
collision_dominance_rows.csv
l2_zero_success_diagnostic.csv
comparison_support_candidates.csv
```

## Support Rules

M1942 is allowed to classify support but not to rank controllers.

Use explicit support labels:

```text
no_support:
  success_count == 0

weak_support:
  0 < success_count < 5

candidate_support:
  success_count >= 5 and offtrack_rate < 0.80

comparison_ready_candidate:
  success_count >= 5
  and episode_count >= 20
  and offtrack_rate < 0.70
  and collision_rate < 0.30
  and at least two profiles in the same scenario slice have nonzero success
```

These are diagnostic labels, not paper claims. A
`comparison_ready_candidate` slice only means a later milestone may design a
controlled comparison on that slice.

## L2 Zero-Success Diagnostic

The all-zero L2 pattern from M1939 must be localized without overclaiming.

M1942 should report:

```text
L2 total success count
L2 offtrack count
L2 collision count
L2 by tier/role/surface/label
non-L2 success count on the same tier/role/surface/label slices
same-source profile contrast rows where any non-L2 profile succeeds and all L2 profiles fail
```

Allowed conclusion:

```text
The current public panel shows an L2 zero-success diagnostic pattern in these
slices.
```

Forbidden conclusion:

```text
Finite-window profiles are worse than current/GRU profiles.
```

That requires balanced support, fresh evaluation, and a comparison manifest.

## Command For M1942

M1942 should implement and run:

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

M1942 may add focused unit tests with synthetic rows before running the real
no-rerun localizer.

## Required Artifacts For M1942

```text
src/autodrift/executable_v2_task_quality_measured_outcome_localization.py
tests/test_executable_v2_task_quality_measured_outcome_localization.py
runs/m1942_executable_v2_task_quality_measured_outcome_localization/summary.json
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_profile.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_tier.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_role.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_surface.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_sampled_label.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_profile_tier.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_profile_role.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_profile_surface.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_profile_sampled_label.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_tier_role_surface.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/outcome_by_candidate_source_profile.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/success_source_rows.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/offtrack_dominance_rows.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/collision_dominance_rows.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/l2_zero_success_diagnostic.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/comparison_support_candidates.csv
runs/m1942_executable_v2_task_quality_measured_outcome_localization/claim_boundary.csv
```

## Pass Gates For M1942

M1942 passes only if:

```text
result_class == task_quality_measured_outcome_localization_pass
source_result_class == task_quality_measured_execution_pass
episode_count == 960
target_episode_count == 960
profile_count == 12
target_profile_count == 12
tier_count == 5
target_tier_count == 5
role_count == 4
target_role_count == 4
surface_count == 2
target_surface_count == 2
all_selected_metrics_finite == true
outcome_counts_match_source_summary == true
required_aggregate_files_written == true
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

If any pass gate fails, M1942 must preserve the partial artifacts and route to
failure audit. It must not repair the source data or rerun M1938.

## Decision Rule After M1942

M1943 should audit the localization result and choose one route:

```text
comparison_design:
  only if at least one comparison_ready_candidate slice exists and direct
  ranking remains blocked until a pre-registered comparison run.

task_quality_repair:
  if successes exist but are too sparse and off-track dominance is localized to
  repairable task geometry or termination semantics.

scenario_redesign:
  if off-track dominance remains broad across profiles/tier/role/surface and
  no useful support slice exists.

support_collection:
  if the panel has meaningful near-support but not enough same-slice profile
  support for comparison.
```

## Claim Boundary

M1941 supports only:

```text
a bounded no-rerun localization route is defined for M1938 measured outcomes.
```

M1941 does not support:

- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification;
- any claim that L2 is worse or that GRU is better.

## Next

Next milestone:

```text
m1942-executable-v2-task-quality-measured-outcome-localization-implementation-and-run
```

M1942 may implement the no-rerun localizer, run focused tests, and execute the
localizer over M1938 artifacts. It must not perform reset, rollout, training,
replay, PPO, profile tuning, or ranking.
