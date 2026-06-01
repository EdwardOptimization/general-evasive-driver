# M2309 Paper-Route Current-Sim Scenario Task-Family Guarded-Repair Target/Guardrail Slice Diagnosis Implementation

- status: completed
- result_class: `current_sim_scenario_task_family_guarded_repair_slice_diagnosis_pass`
- manifest: `experiments/manifests/m2309-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-implementation.json`
- summary: `runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/summary.json`
- runner: `src/autodrift/paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis.py`
- tests: `tests/test_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis.py`
- reset/rollout/policy action: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis \
  --baseline-episode-rows runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution/episode_rows.csv \
  --candidate-episode-rows runs/m2307_paper_route_current_sim_scenario_task_family_guarded_repair_measured_execution/episode_rows.csv \
  --repair-gate-spec runs/m2298_paper_route_current_sim_scenario_task_family_offtrack_primary_collision_guardrail/repair_gate_spec.json \
  --output-dir runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis \
  --next-blocker m2310-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-result-audit
```

## Artifact Completeness

```text
input_episode_count_baseline: 1080
input_episode_count_candidate: 1080
slice_delta_row_count: 31
offtrack_target_slice_count: 20
collision_guardrail_slice_count: 11
guardrail_violation_count: 0
```

M2309 writes:

```text
runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/summary.json
runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/slice_delta_rows.csv
runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/claim_boundary.csv
runs/m2309_paper_route_current_sim_scenario_task_family_guarded_repair_slice_diagnosis/run_state.json
```

## Repair Gate Result

The guarded-v2 repair gate fails:

```text
repair_gate_pass: false
global_offtrack_policy_pass: false
global_collision_policy_pass: false
offtrack_target_policy_pass: false
collision_guardrail_policy_pass: false
```

Global counts:

```text
baseline_global_offtrack_count: 785
candidate_global_offtrack_count: 786
global_offtrack_delta: +1

baseline_global_collision_count: 209
candidate_global_collision_count: 218
global_collision_delta: +9
```

Slice counts:

```text
offtrack_target_nonincrease_count: 9 / 20
offtrack_target_increase_count: 11 / 20
collision_guardrail_nonincrease_count: 4 / 11
collision_guardrail_increase_count: 7 / 11
```

## Largest Violations

Offtrack target increases:

```text
early_far: +10
mid: +5
R0_stable_avoidable: +4
aeb_feasible: +4
left_offset: +4
right_offset: +4
nominal: +4
tire_stiffness_shift: +2
R3_recovery_after_limit: +2
off_track outcome/termination: +1 / +1
```

Collision guardrail increases:

```text
late_close: +15
centerline: +10
low_mu: +8
collision_failure: +9
obstacle_collision: +9
drift_required: +4
right_offset: +3
```

## Interpretation

M2309 makes the M2308 preview durable. The guarded-v2 repair is not merely
below readiness floor; it also fails the actual M2298 target/guardrail repair
gate. This should block another scalar training attempt until a result audit
decides whether to synthesize/pivot or define a materially different repair
route.

## Next

Pre-register:

```text
m2310-paper-route-current-sim-scenario-task-family-guarded-repair-target-guardrail-slice-diagnosis-result-audit
```
