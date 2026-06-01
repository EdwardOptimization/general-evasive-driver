# M2221 Paper-Route Current-Sim Profile/History Failure Diagnosis Implementation

- status: completed
- decision: `current_sim_profile_history_failure_diagnosis_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2221-paper-route-current-sim-profile-history-failure-diagnosis-implementation.json`
- run artifact: `runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_profile_history_failure_diagnosis.py`
- focused tests: `2 passed`
- compile check: `passed`
- reset in M2221: `false`
- measured execution in M2221: `false`
- policy action executed in M2221: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2221 implements and runs the no-rerun profile/history metric diagnosis over
existing M2209/M2218 artifacts. It writes:

```text
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/summary.json
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/profile_failure_metric_summary.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/history_failure_metric_summary.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/profile_pair_delta_metrics.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/l3_failure_mode_breakdown.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/claim_boundary.csv
runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis/run_state.json
```

Summary:

```text
result_class: current_sim_profile_history_failure_diagnosis_pass
episode_row_count: 2304
scene_candidate_count: 9
profile_metric_row_count: 54
history_metric_row_count: 36
pair_delta_row_count: 45
l3_failure_breakdown_row_count: 9
l3_online_success_count: 0
l3_reset_success_count: 0
l2_window_25_success_count: 360
l2_window_50_success_count: 153
l3_zero_success_confirmed: true
l3_reset_equivalent_to_online: true
finite_window_support_visible: true
failure_mode_counts: early_offtrack_failure 21, late_offtrack_or_noncompletion 3, supported_success 30
ranking_admissible_count: 0
winner_selected: false
guardrail_violation_count: 0
```

The success counts are diagnostic row counts over overlapping scene-backed
candidate slices, not a controller-family ranking denominator.

## Interpretation

The public diagnostic slices show a localized recurrent-profile failure:
`L3_online_gru` and `L3_reset_control` have zero successes, and their outcome
counts are equivalent across the L3 failure breakdown. This means the current
diagnostic evidence does not support a history-dependence claim for the L3 GRU
profile on this panel.

The same diagnostic panel does show finite-window support: `L2_window_25` and
`L2_window_50` produce visible success counts. This is useful failure
localization, but it is not a finite-window-vs-GRU verdict because the panel is
still public, diagnostic-only, overlapping, and not ranking-admissible.

## Guardrails

M2221 did not run any new environment reset, rollout, measured execution,
training, replay, PPO, or policy-action execution. It only reanalyzes existing
episode metrics. The implementation explicitly writes claim-boundary artifacts
that keep these claims blocked:

```text
controller-family ranking
winner selection
finite-window vs GRU conclusion
paper-level benchmark result
level3 self-identification
```

## Verification

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_current_sim_profile_history_failure_diagnosis.py
python -m compileall -q src/autodrift/paper_route_current_sim_profile_history_failure_diagnosis.py tests/test_paper_route_current_sim_profile_history_failure_diagnosis.py
PYTHONPATH=src python -m autodrift.paper_route_current_sim_profile_history_failure_diagnosis --episode-rows runs/m2209_paper_route_current_sim_offtrack_support_measured_execution_rerun/episode_rows.csv --diagnostic-summary runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/summary.json --scene-candidate-summary runs/m2218_paper_route_current_sim_bounded_diagnostic_comparison/scene_candidate_summary.csv --output-dir runs/m2221_paper_route_current_sim_profile_history_failure_diagnosis
```

The focused test also checks that `mean_action_rate` is populated in
`profile_failure_metric_summary.csv`.

## Next Step

M2222 should audit the M2221 result before any repair, rerun, profile ranking,
or paper-route conclusion. Given the current result, the likely next branch is
a recurrent-profile checkpoint/config/training audit: first determine why the
L3 online GRU and reset-control profiles are both zero-success and equivalent,
then decide whether to repair/retrain the recurrent profile or treat it as a
bounded negative result.
