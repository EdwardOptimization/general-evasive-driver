# M2364 Paper-Route Current-Sim Dual-Axis Measured Outcome Localization Design

- status: completed
- decision: `measured_outcome_localization_design_admit_artifact_only_implementation`
- manifest: `experiments/manifests/m2364-paper-route-current-sim-dual-axis-measured-outcome-localization-design.json`
- parent audit: `docs/m2363-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-result-audit.md`
- reset/rollout/measured execution in M2364: `false`
- policy action executed in M2364: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2364 designs an artifact-only localization pass over the complete M2362
measured panel:

```text
source summary:
  runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json

source episodes:
  runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/episode_rows.csv

source episode_count:
  5400
```

It does not rerun reset, rollout, policy actions, training, replay, or PPO.

The goal is to turn the M2363 outcome audit into explicit target and guardrail
slices before any repair design.

## Slice Classes

M2365 should classify slices into three route classes:

```text
offtrack_target:
  high offtrack rate slices that should become repair targets.

collision_guardrail:
  non-R4 slices where collision rate is high enough that an offtrack repair
  must not make collision worse.

r4_mitigation_semantics:
  R4 unavoidable mitigation slices, where collision dominance should be audited
  with mitigation-specific semantics rather than mixed into offtrack repair.
```

M2365 should preserve diagnostic-only profile and pack information, but must not
rank profiles or select a winner.

## Candidate Slice Axes

M2365 should compute aggregate rows for these axes:

```text
global
pack_id
profile_name
role_family
scenario_family_id
sampled_obstacle_label
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
sampling_repair_class
pack_id + role_family
profile_name + role_family
role_family + hidden_dynamics_bucket
role_family + obstacle_longitudinal_timing_bucket
role_family + obstacle_lateral_offset_bucket
pack_id + profile_name + role_family
```

Each slice row should include:

```text
slice_axis
slice_key
slice_value
episode_count
success_count / success_rate
collision_count / collision_rate
offtrack_count / offtrack_rate
max_step_noncompletion_count / rate
other_failure_count / rate
dominant_failure_mode
route_class
priority_score
diagnostic_only
ranking_admissible
winner_selected
paper_level_claim_made
finite_window_vs_gru_conclusion_made
level3_self_id_claim_made
```

## Initial Thresholds

Use bounded thresholds, not tuned profile-specific rules:

```text
minimum_slice_episode_count: 30
offtrack_target_threshold: offtrack_rate >= 0.70
high_priority_offtrack_threshold: offtrack_rate >= 0.85
collision_guardrail_threshold: collision_rate >= 0.15
r4_semantics_selector: role_family == R4_unavoidable_mitigation
```

Route priority:

```text
priority_score =
  episode_count_weighted_failure_mass
  + high_priority_threshold_bonus
  + role_priority_bonus
```

The implementation may keep this simple and deterministic. It should not tune
thresholds after seeing output.

## Required Outputs

M2365 should write:

```text
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/summary.json
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/offtrack_target_slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/collision_guardrail_slice_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/r4_mitigation_semantics_rows.csv
runs/m2365_paper_route_current_sim_dual_axis_measured_outcome_localization/claim_boundary.csv
```

## Frozen M2365 Command

M2365 should implement and run:

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

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_measured_outcome_localization.py
```

## Pass Gates

M2365 passes only if:

```text
source_episode_count == 5400
slice_row_count > 0
offtrack_target_slice_count > 0
r4_mitigation_semantics_slice_count > 0
collision_guardrail_slice_count >= 0
ranking_admissible_count == 0
winner_selected_count == 0
guardrail_violation_count == 0
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
```

Pass or fail, M2365 must route to M2366 result audit before any repair.

## Claim Boundary

M2364 supports only:

```text
artifact-only outcome localization design over M2362 measured artifacts.
```

M2365, if it passes, may claim only:

```text
M2362 outcomes have been localized into diagnostic target and guardrail slices.
```

Still blocked:

```text
controller ranking;
winner selection;
paper-level benchmark evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence;
scenario redesign executed;
training repair success.
```

## Next

Pre-register:

```text
m2365-paper-route-current-sim-dual-axis-measured-outcome-localization-implementation
```
