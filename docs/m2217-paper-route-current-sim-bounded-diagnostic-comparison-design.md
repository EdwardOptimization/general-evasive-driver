# M2217 Paper-Route Current-Sim Bounded Diagnostic Comparison Design

- status: completed
- decision: `current_sim_bounded_diagnostic_comparison_design_admit_no_rerun_implementation`
- manifest: `experiments/manifests/m2217-paper-route-current-sim-bounded-diagnostic-comparison-design.json`
- parent audit: `docs/m2216-paper-route-current-sim-support-slice-validity-audit-result-audit.md`
- reset in M2217: `false`
- measured execution in M2217: `false`
- policy action executed in M2217: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2217 freezes a no-rerun diagnostic comparison over M2215
`scene_backed_candidate` slices. The goal is not to rank profiles. The goal is
to determine whether the scene-backed support is broad enough to justify a
future comparison route or whether it only diagnoses profile/task weaknesses.

## Inputs

M2218 should read:

```text
runs/m2215_paper_route_current_sim_support_slice_validity_audit/summary.json
runs/m2215_paper_route_current_sim_support_slice_validity_audit/scene_backed_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/history_family_diagnostic_candidates.csv
runs/m2215_paper_route_current_sim_support_slice_validity_audit/profile_only_candidates.csv
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv
```

No environment reset, rollout, policy action, measured execution, training,
replay, PPO, checkpoint promotion, or actor input/output change is allowed.

## Scene-Backed Filter

Only rows from `scene_backed_candidates.csv` may define diagnostic slices. For
each row, parse `group_key` and `group_value` into filters:

```text
task_family=T1_reactive_emergency_avoidance
source_family_template=t4_actuator_delay_response
capability_pair=reactive_current_response
```

Then select matching rows from M2209 `episode_rows.csv`. Rows from
`history_family_diagnostic_candidates.csv` and `profile_only_candidates.csv`
are context only and must not define comparison slices.

## Diagnostic Tables

M2218 should write these diagnostic tables:

```text
scene_candidate_summary.csv:
  one row per scene-backed candidate, with total outcomes and diagnostic labels

scene_candidate_profile_matrix.csv:
  scene-backed candidate x profile_name outcomes

scene_candidate_history_matrix.csv:
  scene-backed candidate x history_representation outcomes

scene_candidate_profile_history_matrix.csv:
  scene-backed candidate x profile_name x history_representation outcomes

diagnostic_claim_boundary.csv:
  explicit allowed/blocked claims
```

Every table row must include:

```text
diagnostic_only: true
ranking_admissible: false
winner_selected: false
controller_family_ranking_claim_made: false
```

## Diagnostic Labels

Each scene-backed candidate should get one primary diagnostic label:

```text
multi_profile_diagnostic_support:
  episode_count >= 64
  success_count >= 24
  at least 2 profile_name values have success_count >= 8
  offtrack_rate <= 0.80

profile_concentrated_support:
  episode_count >= 64
  success_count >= 24
  one profile contributes >= 0.75 of all successes

history_family_concentrated_support:
  episode_count >= 64
  success_count >= 24
  one history_representation contributes >= 0.75 of all successes

offtrack_dominated_diagnostic:
  offtrack_rate >= 0.75

low_support_diagnostic:
  success_count < 24

mixed_diagnostic:
  none of the above
```

These labels are routing signals only. They are not rank, promotion, or paper
claims.

## Summary Metrics

M2218 summary should report:

```text
scene_candidate_count
diagnostic_row_count
multi_profile_diagnostic_support_count
profile_concentrated_support_count
history_family_concentrated_support_count
offtrack_dominated_diagnostic_count
low_support_diagnostic_count
ranking_admissible_count
winner_selected
guardrail_violation_count
```

## Routing Rule

After M2218:

```text
if multi_profile_diagnostic_support_count > 0:
  route to result audit, then possibly a bounded public diagnostic report.

if profile_concentrated_support_count > 0 and multi_profile_diagnostic_support_count == 0:
  route to profile/task diagnostic repair, not controller ranking.

if history_family_concentrated_support_count > 0:
  route to history-representation diagnostic audit, not finite-window vs GRU verdict.

if offtrack_dominated_diagnostic_count dominates:
  route to task-quality repair or stop this current-sim comparison panel.
```

## Claim Boundary

Allowed claim after M2218:

```text
Scene-backed M2215 candidate slices have been converted into no-rerun diagnostic
tables with explicit blocked ranking claims.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
checkpoint/profile promotion;
private-holdout generalization.
```

## Next Step

M2218 may implement and run the no-rerun diagnostic comparison:

```text
PYTHONPATH=src python -m autodrift.paper_route_current_sim_bounded_diagnostic_comparison \
  --episode-rows runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv \
  --scene-backed-candidates runs/m2215_paper_route_current_sim_support_slice_validity_audit/scene_backed_candidates.csv \
  --validity-summary runs/m2215_paper_route_current_sim_support_slice_validity_audit/summary.json \
  --output-dir runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison
```
