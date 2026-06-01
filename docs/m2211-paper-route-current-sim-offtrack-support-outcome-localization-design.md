# M2211 Paper-Route Current-Sim Offtrack-Support Outcome Localization Design

- status: completed
- decision: `current_sim_offtrack_support_outcome_localization_design_admit_implementation`
- manifest: `experiments/manifests/m2211-paper-route-current-sim-offtrack-support-outcome-localization-design.json`
- parent audit: `docs/m2210-paper-route-current-sim-offtrack-support-measured-execution-rerun-result-audit.md`
- measured execution in M2211: `false`
- policy action executed in M2211: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2211 freezes a no-rerun localization step over M2209 artifacts:

```text
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv
```

The goal is to localize why the repaired panel remains offtrack dominated
before another task repair, rerun, or comparison design.

## Inputs

Required inputs:

```text
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/summary.json
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/profile_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/task_family_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/source_family_template_aggregate.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/capability_pair_aggregate.csv
```

Expected audited counts:

```text
episode_count: 2304
profile_count: 8
spec_count: 288
success_obstacle_pass: 374
collision_failure: 49
off_track_noncollision_noncompletion: 1881
```

## Group Keys

M2212 should aggregate outcome support over these group keys:

```text
overall
task_family
source_family_template
capability_pair
profile_name
history_representation
profile_level
task_family x history_representation
task_family x profile_name
source_family_template x history_representation
source_family_template x profile_name
capability_pair x history_representation
capability_pair x profile_name
```

The profile-containing groups are diagnostic context only. They must not be
used to rank or select a winning controller.

## Support Labels

M2212 should classify each group into exactly one primary support label:

```text
comparison_ready_candidate
candidate_support
offtrack_dominated
collision_dominated
low_success_support
low_sample_count
mixed_unresolved
```

Suggested deterministic rules:

```text
low_sample_count:
  episode_count < 32

comparison_ready_candidate:
  episode_count >= 64
  success_count >= 24
  success_rate >= 0.25
  offtrack_rate <= 0.60
  collision_rate <= 0.20

candidate_support:
  episode_count >= 64
  success_count >= 8
  success_rate >= 0.10
  offtrack_rate <= 0.80

offtrack_dominated:
  offtrack_rate >= 0.75
  or offtrack_count >= 3 * max(success_count, 1)

collision_dominated:
  collision_rate >= 0.25

low_success_support:
  success_count < 8
  or success_rate < 0.10

mixed_unresolved:
  none of the above
```

The `comparison_ready_candidate` label is still not a ranking decision. It only
marks slices that may deserve a later denominator-backed comparison design.

## Required Output Artifacts

M2212 should write:

```text
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/summary.json
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/group_outcome_support.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/comparison_ready_candidate_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/offtrack_dominated_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/collision_dominated_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/low_success_support_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/claim_boundary.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/run_state.json
```

Summary should report:

```text
input_episode_count
overall_success_rate
overall_collision_rate
overall_offtrack_rate
comparison_ready_candidate_count
candidate_support_count
offtrack_dominated_count
collision_dominated_count
low_success_support_count
low_sample_count
guardrail_violation_count
controller_family_ranking_claim_made: false
finite_window_vs_gru_conclusion_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Claim Boundary

Allowed claim after M2212:

```text
M2209 outcome support has been localized into support/blocker slices without
rerun or profile ranking.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2212 may implement this no-rerun localization. If localization shows no
comparison-ready slices, the next route should be task-quality repair or branch
synthesis rather than another direct comparison attempt.
