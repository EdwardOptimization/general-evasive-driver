# M2313 Paper-Route Current-Sim Scenario Task-Family Feasibility Calibration Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_feasibility_calibration_pass`
- manifest: `experiments/manifests/m2313-paper-route-current-sim-scenario-task-family-feasibility-calibration-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_scenario_task_family_feasibility_calibration.py`
- tests: `tests/test_paper_route_current_sim_scenario_task_family_feasibility_calibration.py`
- summary: `runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/summary.json`
- reset/rollout/policy action: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_feasibility_calibration \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration \
  --eval-seed-base 231300 \
  --support-policies aeb aes envelope_aes \
  --seed-repeats 5 \
  --target-scenario-spec-count 72 \
  --target-support-policy-count 3 \
  --target-episode-count 1080 \
  --next-blocker m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit
```

## Artifact Completeness

```text
episode_count: 1080
target_episode_count: 1080
scenario_spec_count: 72
support_policy_count: 3
seed_repeat_count: 5
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
```

M2313 writes:

```text
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/summary.json
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/support_aggregate_rows.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/scenario_support_labels.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/role_support_summary.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/claim_boundary.csv
runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/run_state.json
```

## Global Diagnostic Outcome

Support-policy diagnostic outcomes:

```text
global_success_count: 107
global_collision_count: 468
global_offtrack_count: 393
global_obstacle_completed_count: 107

global_success_rate: 0.09907407407407408
global_collision_rate: 0.43333333333333335
global_offtrack_rate: 0.3638888888888889
```

Outcome buckets:

```text
collision_failure: 468
off_track_noncollision_noncompletion: 393
speed_too_low_noncollision_noncompletion: 92
max_steps_noncompletion: 20
success_obstacle_pass: 107
```

This is not a controller-family ranking. The support policies are diagnostic
support bounds only.

## Support Labels

Scenario-level support labels:

```text
support_clear: 12
support_mixed: 26
support_blocked: 21
metric_conflict: 13
```

Role support summary:

```text
R0_stable_avoidable:
  support_clear: 0
  support_mixed: 0
  support_blocked: 0
  metric_conflict: 12

R1_aeb_infeasible_stable_aes:
  support_clear: 12
  support_mixed: 0
  support_blocked: 0
  metric_conflict: 0

R2_handling_limit_drift_capable_avoidance:
  support_clear: 0
  support_mixed: 7
  support_blocked: 5
  metric_conflict: 0

R3_recovery_after_limit:
  support_clear: 0
  support_mixed: 8
  support_blocked: 3
  metric_conflict: 1

R4_unavoidable_mitigation:
  support_clear: 0
  support_mixed: 3
  support_blocked: 9
  metric_conflict: 0

R5_hidden_dynamics_robustness:
  support_clear: 0
  support_mixed: 8
  support_blocked: 4
  metric_conflict: 0
```

The strongest immediate signal is that every R0 AEB-feasible scenario is marked
`metric_conflict`: support policies can avoid collision/offtrack in some cases
by stopping or becoming speed-limited, but the panel's success semantics require
`success_obstacle_pass`. This must be audited before using R0 as ordinary
driver-performance evidence.

## Claim Boundary

Admissible:

```text
scenario_task_family_support_policy_feasibility_calibration_completed
```

Not admissible:

```text
controller_family_ranking
winner_selection
paper_level_benchmark_result
finite_window_vs_gru_conclusion
level3_self_identification
```

## Next

Pre-register:

```text
m2314-paper-route-current-sim-scenario-task-family-feasibility-calibration-result-audit
```
