# M2318 Paper-Route Current-Sim Scenario Task-Family Role Success Semantics Repair Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_role_success_semantics_repair_pass`
- manifest: `experiments/manifests/m2318-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-implementation.json`
- design doc: `docs/m2317-paper-route-current-sim-scenario-task-family-role-success-semantics-repair-design.md`
- summary: `runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair/summary.json`
- helper: `src/autodrift/paper_route_current_sim_scenario_task_family_role_success_semantics.py`
- rescore runner: `src/autodrift/paper_route_current_sim_scenario_task_family_role_success_semantics_repair.py`
- focused tests: `tests/test_paper_route_current_sim_scenario_task_family_role_success_semantics.py`
- reset/rollout/policy action in M2318: `false`
- training/replay/PPO in M2318: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2318 adds a bounded role-success helper:

```text
raw_obstacle_pass_success(row)
is_collision(row)
is_offtrack(row)
is_r0_safe_stop_success(row)
role_success(row)
role_success_reason(row)
role_success_outcome_bucket(row)
annotate_role_success(row)
```

The R0 safe-stop rule is:

```text
role_family == R0_stable_avoidable
termination_reason == speed_too_low
min_clearance_margin > 0.0
collision == false
offtrack == false
```

The helper is now wired into:

```text
paper_route_current_sim_scenario_task_family_feasibility_calibration.py
paper_route_current_sim_scenario_task_family_measured_execution.py
paper_route_current_sim_scenario_task_family_failure_slice_diagnosis.py
```

Episode rows now expose:

```text
raw_success
role_success
role_success_reason
role_success_outcome_bucket
success
```

`success` is the repaired role success for current-sim task-family diagnostics;
`raw_success` preserves the original obstacle-pass success value.

## Command

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_scenario_task_family_role_success_semantics.py
```

Artifact-only rescore:

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_role_success_semantics_repair \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --episode-rows runs/m2313_paper_route_current_sim_scenario_task_family_feasibility_calibration/episode_rows.csv \
  --output-dir runs/m2318_paper_route_current_sim_scenario_task_family_role_success_semantics_repair \
  --target-episode-count 1080 \
  --target-scenario-spec-count 72 \
  --next-blocker m2319-paper-route-current-sim-scenario-task-family-feasibility-calibration-branch-synthesis
```

## Rescore Result

M2318 rescored the existing M2313 artifacts only:

```text
input_episode_count: 1080
rescored_episode_count: 1080
scenario_spec_count: 72
support_policy_count: 3
seed_repeats: 5
guardrail_violation_count: 0
```

Support labels changed as intended:

```text
baseline_support_label_counts:
  support_clear: 12
  support_mixed: 26
  support_blocked: 21
  metric_conflict: 13

repaired_support_label_counts:
  support_clear: 24
  support_mixed: 26
  support_blocked: 21
  metric_conflict: 1

support_clear_delta: 12
metric_conflict_delta: -12
```

R0-specific gates:

```text
r0_support_clear_count: 12
r0_metric_conflict_count: 0
r0_aeb_role_success_count: 60
r0_safe_stop_success_count: 62
non_r0_safe_stop_success_count: 0
```

Role support summary after repair:

```text
R0_stable_avoidable: support_clear 12 / 12
R1_aeb_infeasible_stable_aes: support_clear 12 / 12
R2_handling_limit_drift_capable_avoidance: support_mixed 7 / 12, support_blocked 5 / 12
R3_recovery_after_limit: support_mixed 8 / 12, support_blocked 3 / 12, metric_conflict 1 / 12
R4_unavoidable_mitigation: support_mixed 3 / 12, support_blocked 9 / 12
R5_hidden_dynamics_robustness: support_mixed 8 / 12, support_blocked 4 / 12
```

## Claim Boundary

Allowed claim:

```text
M2318 implements bounded R0 safe-stop role-success semantics and artifact-only
rescoring over M2313 support-policy artifacts.
```

Blocked claims:

```text
new rollout result;
driver performance improvement;
controller-family ranking;
checkpoint promotion;
paper-level current-sim evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence;
R2-R5 support solved.
```

## Follow-Up

Pre-register branch synthesis:

```text
experiments/manifests/m2319-paper-route-current-sim-scenario-task-family-feasibility-calibration-branch-synthesis.json
```
