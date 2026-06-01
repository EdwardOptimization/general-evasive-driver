# M2214 Paper-Route Current-Sim Support-Slice Validity Audit Design

- status: completed
- decision: `current_sim_support_slice_validity_audit_design_admit_no_rerun_implementation`
- manifest: `experiments/manifests/m2214-paper-route-current-sim-support-slice-validity-audit-design.json`
- parent synthesis: `docs/m2213-paper-route-current-sim-offtrack-support-outcome-localization-branch-synthesis.md`
- reset in M2214: `false`
- measured execution in M2214: `false`
- policy action executed in M2214: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2214 freezes a no-rerun validity audit for the support slices produced by
M2212. The audit must answer whether the `comparison_ready_candidate` labels are
usable scene-backed evidence, profile-only artifacts, or narrower diagnostic
signals.

This audit is required before any new task repair, controller-family comparison,
finite-window vs GRU conclusion, paper claim, or self-ID claim.

## Inputs

M2215 should read only existing artifacts:

```text
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/summary.json
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/group_outcome_support.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/comparison_ready_candidate_slices.csv
runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/offtrack_dominated_slices.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv
```

No environment reset, rollout, policy action, measured execution, training,
replay, PPO, or checkpoint change is allowed.

## Validity Labels

Each M2212 group row should receive exactly one validity label:

```text
scene_backed_candidate:
  support_label in {comparison_ready_candidate, candidate_support}
  group_key does not include profile_name, profile_level, or history_representation
  profile_count >= 4
  history_representation_count >= 2
  task_source_count >= 16
  episode_count >= 64

history_family_diagnostic:
  support_label in {comparison_ready_candidate, candidate_support}
  group_key includes history_representation
  group_key does not include profile_name
  profile_count >= 2
  episode_count >= 64

profile_only_candidate:
  support_label in {comparison_ready_candidate, candidate_support}
  group_key includes profile_name or profile_level
  episode_count >= 64

denominator_imbalanced:
  support_label in {comparison_ready_candidate, candidate_support}
  but profile_count < 2, history_representation_count < 1, task_source_count < 16,
  or episode_count < 64

global_or_scene_blocker:
  group_key is overall, task_family, source_family_template, or capability_pair
  and support_label is offtrack_dominated, collision_dominated, or low_success_support

low_sample_or_unresolved:
  support_label is low_sample_count or mixed_unresolved

invalid_for_ranking:
  any remaining row
```

The label order matters. `scene_backed_candidate` is the only label that can
admit a later bounded comparison design, and even that later comparison remains
public diagnostic evidence until holdout/generalization gates exist.

## Denominator Checks

The audit should report these booleans per row:

```text
contains_profile_axis
contains_history_axis
contains_profile_level_axis
profile_denominator_balanced
history_denominator_balanced
task_source_denominator_sufficient
ranking_admissible
```

`ranking_admissible` must remain `false` for M2215. M2215 is a validity audit,
not a comparison.

For summary routing, report:

```text
scene_backed_candidate_count
history_family_diagnostic_count
profile_only_candidate_count
denominator_imbalanced_count
global_or_scene_blocker_count
ranking_admissible_count
guardrail_violation_count
```

## Output Artifacts

M2215 should write:

```text
runs/m2215_paper_route_current_sim_support_slice_validity_audit/summary.json
runs/m2215_paper_route_current_sim_support_slice_validity_audit/slice_validity.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/scene_backed_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/history_family_diagnostic_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/profile_only_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/denominator_imbalanced_slices.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/global_or_scene_blockers.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/claim_boundary.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/run_state.json
```

## Routing Rule

After M2215:

```text
if scene_backed_candidate_count > 0 and ranking_admissible_count == 0:
  route to bounded diagnostic comparison design for those scene-backed slices,
  still no paper claim.

if scene_backed_candidate_count == 0 and history_family_diagnostic_count > 0:
  route to task/profile diagnostic audit; do not compare controllers globally.

if scene_backed_candidate_count == 0 and profile_only_candidate_count > 0:
  route to profile-artifact audit or task-quality repair; do not rank.

if all support is offtrack/collision/low-sample:
  route to task-quality repair or stop this current-sim comparison branch.
```

## Claim Boundary

Allowed claim after M2215:

```text
M2212 support slices have been classified by validity type without rerun or
ranking.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
profile promotion;
new task-quality repair without using the validity audit.
```

## Next Step

M2215 may implement and run this no-rerun audit:

```text
PYTHONPATH=src python -m autodrift.paper_route_current_sim_support_slice_validity_audit \
  --group-support runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/group_outcome_support.csv \
  --summary runs/m2212_paper_route_current_sim_offtrack_support_outcome_localization/summary.json \
  --episode-rows runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv \
  --output-dir runs/m2215_paper_route_current_sim_support_slice_validity_audit
```
