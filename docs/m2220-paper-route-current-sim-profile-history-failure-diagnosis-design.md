# M2220 Paper-Route Current-Sim Profile/History Failure Diagnosis Design

- status: completed
- decision: `current_sim_profile_history_failure_diagnosis_design_admit_no_rerun_implementation`
- manifest: `experiments/manifests/m2220-paper-route-current-sim-profile-history-failure-diagnosis-design.json`
- parent synthesis: `docs/m2219-paper-route-current-sim-bounded-diagnostic-comparison-branch-synthesis.md`
- reset in M2220: `false`
- measured execution in M2220: `false`
- policy action executed in M2220: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2220 freezes a no-rerun metric diagnosis over the M2218 scene-backed
diagnostic slices. The goal is to explain the observed diagnostic pattern:

```text
L3_online_gru and L3_reset_control: zero visible successes
L2_window_25 and L2_window_50: visible support
```

This is not a controller ranking and not a finite-window vs GRU verdict. It is
a failure-mode audit to decide whether the next useful branch is profile
training/config repair, task-quality repair, or a bounded diagnostic report.

## Inputs

M2221 should read only existing artifacts:

```text
runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/summary.json
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_summary.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_profile_matrix.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_history_matrix.csv
runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_profile_history_matrix.csv
```

No reset, rollout, policy action, measured execution, training, replay, PPO,
checkpoint promotion, or actor input/output change is allowed.

## Target Profiles And Groups

Primary diagnostic groups:

```text
L3_online_gru
L3_reset_control
L2_window_25
L2_window_50
L0_current_masked
L1_one_step
```

Primary history groups:

```text
online_recurrent_hidden
explicit_finite_window
current_response
one_step_command_response
```

M2221 should evaluate these only inside the M2218 scene-backed candidate slices.
The implementation should use scene candidate filters from
`scene_candidate_summary.csv`, not all M2209 rows.

## Metrics

Per candidate/profile/history group, M2221 should aggregate:

```text
episode_count
success_count
collision_count
offtrack_count
success_rate
collision_rate
offtrack_rate
mean_return
mean_action_rate
mean_min_clearance_margin
mean_max_off_track_overshoot
mean_off_track_severity_proxy
mean_time_to_first_off_track_s
mean_impact_speed_proxy
mean_impact_severity_proxy
mean_high_sideslip_fraction
mean_max_abs_beta
mean_max_abs_yaw_rate
drift_used_rate
recovery_success_rate
```

Non-finite or missing metric values should be counted and left blank/`None` in
strict JSON summaries rather than silently converted to zero.

## Failure-Mode Labels

Each target profile/history group should get one primary failure-mode label:

```text
supported_success:
  success_count >= 8

early_offtrack_failure:
  offtrack_count > success_count
  mean_time_to_first_off_track_s is finite
  mean_time_to_first_off_track_s <= 2.0

late_offtrack_or_noncompletion:
  offtrack_count > success_count
  mean_time_to_first_off_track_s is missing or > 2.0

collision_dominated_failure:
  collision_count >= max(success_count, offtrack_count)

high_instability_failure:
  mean_max_abs_beta >= 0.8 or mean_high_sideslip_fraction >= 0.25

low_support_failure:
  success_count < 8

mixed_failure:
  none of the above
```

The label order should be deterministic. `supported_success` is a diagnostic
support label, not a winner label.

## Pairwise Diagnostic Deltas

M2221 should compute pairwise diagnostic deltas for:

```text
L2_window_25 - L3_online_gru
L2_window_25 - L3_reset_control
L2_window_50 - L3_online_gru
L2_window_50 - L3_reset_control
L3_online_gru - L3_reset_control
```

Allowed delta fields:

```text
success_rate_delta
offtrack_rate_delta
collision_rate_delta
mean_time_to_first_off_track_delta
mean_min_clearance_margin_delta
mean_action_rate_delta
mean_max_abs_beta_delta
```

These are diagnostic deltas only. They must include:

```text
diagnostic_only: true
ranking_admissible: false
winner_selected: false
finite_window_vs_gru_conclusion_made: false
```

## Output Artifacts

M2221 should write:

```text
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/summary.json
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/profile_failure_metric_summary.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/history_failure_metric_summary.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/profile_pair_delta_metrics.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/l3_failure_mode_breakdown.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/claim_boundary.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/run_state.json
```

Summary should report:

```text
target_profile_count
scene_candidate_count
l3_online_success_count
l3_reset_success_count
l2_window_25_success_count
l2_window_50_success_count
l3_zero_success_confirmed
l3_reset_equivalent_to_online
finite_window_support_visible
ranking_admissible_count
winner_selected
guardrail_violation_count
```

## Routing Rule

After M2221:

```text
if l3_zero_success_confirmed and l3_reset_equivalent_to_online:
  route to recurrent-profile checkpoint/config/training audit.

if l3_zero_success_confirmed and reset differs from online:
  route to recurrent-state/path-dependence diagnostic audit.

if finite_window_support_visible but concentrated in one profile:
  route to finite-window profile diagnostic, not a verdict.

if all profiles are low support:
  route to task-quality repair or stop current panel.
```

## Claim Boundary

Allowed claim after M2221:

```text
The current public diagnostic panel localizes profile/history failure modes
using existing measured episode metrics.
```

Still blocked:

```text
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark result;
level3 self-identification;
checkpoint/profile promotion;
new training or repair.
```

## Next Step

M2221 may implement and run the no-rerun profile/history failure diagnosis:

```text
PYTHONPATH=src python -m autodrift.paper_route_current_sim_profile_history_failure_diagnosis \
  --episode-rows runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv \
  --diagnostic-summary runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/summary.json \
  --scene-candidate-summary runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_summary.csv \
  --output-dir runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis
```
