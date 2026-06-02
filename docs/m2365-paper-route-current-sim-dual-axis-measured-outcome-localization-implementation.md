# M2365 Paper-Route Current-Sim Dual-Axis Measured Outcome Localization Implementation

- status: completed
- result_class: `current_sim_dual_axis_measured_outcome_localization_pass`
- manifest: `experiments/manifests/m2365-paper-route-current-sim-dual-axis-measured-outcome-localization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_measured_outcome_localization.py`
- focused tests: `2 passed`
- source summary: `runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json`
- source episode rows: `runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/episode_rows.csv`
- output summary: `runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json`
- reset/rollout/measured execution in M2365: `false`
- policy action executed in M2365: `false`
- training/replay/PPO: `false`
- ranking/winner/paper/FW-vs-GRU/level3 self-ID claims: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_measured_outcome_localization \
  --summary runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json \
  --episode-rows runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/episode_rows.csv \
  --output-dir runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization \
  --target-episode-count 5400 \
  --minimum-slice-episode-count 30 \
  --offtrack-target-threshold 0.70 \
  --high-priority-offtrack-threshold 0.85 \
  --collision-guardrail-threshold 0.15 \
  --next-blocker m2366-paper-route-current-sim-dual-axis-measured-outcome-localization-result-audit
```

## Result

```text
source_episode_count: 5400
slice_row_count: 313
offtrack_target_slice_count: 198
collision_guardrail_slice_count: 95
r4_mitigation_semantics_slice_count: 48
high_priority_offtrack_slice_count: 99
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Route class counts:

```text
offtrack_target: 118
offtrack_target_with_collision_guardrail: 80
collision_guardrail: 15
r4_mitigation_semantics: 48
diagnostic_only: 52
```

## Localized Slices

Top high-priority offtrack targets include:

```text
obstacle_longitudinal_timing_bucket=early_far:
  episode_count 1800, offtrack_rate 0.8778, collision_rate 0.0478

role_family=R0_stable_avoidable:
  episode_count 900, offtrack_rate 0.9344, collision_rate 0.0011

scenario_family_id=R0:
  episode_count 900, offtrack_rate 0.9344, collision_rate 0.0011

hidden_dynamics_bucket=nominal_neighbor:
  episode_count 465, offtrack_rate 0.8559, collision_rate 0.1355
```

Top mixed offtrack target plus collision guardrail slices include:

```text
global=all:
  episode_count 5400, offtrack_rate 0.7263, collision_rate 0.1996

sampled_obstacle_label=drift_required:
  episode_count 2025, offtrack_rate 0.7867, collision_rate 0.2015

profile_name=L2_window_50:
  episode_count 1080, offtrack_rate 0.7139, collision_rate 0.2250
```

R4 remains a separate mitigation-semantics route:

```text
role_family=R4_unavoidable_mitigation:
  episode_count 900, offtrack_rate 0.2611, collision_rate 0.7389

scenario_family_id=R4:
  episode_count 900, offtrack_rate 0.2611, collision_rate 0.7389

sampled_obstacle_label=unavoidable:
  episode_count 900, offtrack_rate 0.2611, collision_rate 0.7389
```

## Artifacts

```text
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/offtrack_target_slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/collision_guardrail_slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/r4_mitigation_semantics_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/claim_boundary.csv
```

## Claim Boundary

M2365 may claim only:

```text
M2362 measured outcomes have been localized into diagnostic target and
guardrail slices.
```

Still blocked:

```text
controller-family ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Next

Pre-registered follow-up:

```text
m2366-paper-route-current-sim-dual-axis-measured-outcome-localization-result-audit
```

M2366 must audit the M2365 slice panel before any scenario repair, training,
ranking, or paper-route interpretation.
