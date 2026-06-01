# M2255 Paper-Route Current-Sim Offtrack Failure-Slice Diagnosis Design

- status: completed
- decision: `current_sim_offtrack_failure_slice_diagnosis_design_admit_no_rerun_implementation`
- manifest: `experiments/manifests/m2255-paper-route-current-sim-offtrack-failure-slice-diagnosis-design.json`
- parent synthesis: `docs/m2254-paper-route-current-sim-offtrack-recovery-corridor-branch-synthesis.md`

## Design Rationale

M2254 closed the bounded offtrack/recovery/corridor scalar reward branch:

```text
M2244 baseline success/offtrack/collision: 277/110/93
M2253 repaired success/offtrack/collision: 269/118/93
mean return delta: +14.37612
```

The next step must not be another training run or reward tweak. The next step is
a no-rerun slice diagnosis over existing episode rows to explain where the
offtrack regression came from.

## Input Artifacts

M2256 should use exactly:

```text
baseline panel:
  runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv
  runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/profile_seed_aggregate.csv

repaired panel:
  runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/episode_rows.csv
  runs/m2253_paper_route_current_sim_offtrack_recovery_corridor_selected_checkpoint_outcome_localization/profile_seed_aggregate.csv
```

Expected support:

```text
baseline episode rows: 480
repaired episode rows: 480
profile_seed groups per panel: 15
episodes per profile_seed group: 32
```

No environment reset, rollout, training, replay, PPO, or checkpoint loading is
allowed in M2256.

## Slice Axes

M2256 should compute deltas between `baseline_m2244` and `repaired_m2253` for:

```text
global
profile_name
profile_name|seed_id
selected_readiness_floor_pass
outcome_bucket
termination_reason
obstacle_label
```

Offtrack timing buckets:

```text
no_offtrack
early_offtrack: time_to_first_off_track_s <= 1.20
mid_offtrack: 1.20 < time_to_first_off_track_s <= 1.70
late_offtrack: time_to_first_off_track_s > 1.70
unknown_offtrack_time
```

Offtrack severity buckets from `max_off_track_overshoot`:

```text
no_offtrack_overshoot
trace_overshoot: 0 < overshoot <= 0.02
mild_overshoot: 0.02 < overshoot <= 0.05
severe_overshoot: overshoot > 0.05
unknown_overshoot
```

Clearance risk buckets from `min_clearance_margin`:

```text
collision
negative_clearance_margin
low_clearance_margin: 0 <= margin < 0.25
medium_clearance_margin: 0.25 <= margin < 1.0
safe_clearance_margin: margin >= 1.0
unknown_clearance_margin
```

Sidedness and recovery proxies:

```text
left_curve_steps > 0
right_curve_steps > 0
high_sideslip_fraction bucket: zero / low / high
recovery_success
drift_used
controlled_drift_recovery_success
```

## Required Outputs

M2256 should write:

```text
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/summary.json
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/panel_summary.csv
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/global_delta.csv
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/profile_seed_delta.csv
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/outcome_delta.csv
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/offtrack_timing_delta.csv
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/offtrack_severity_delta.csv
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/clearance_risk_delta.csv
runs/m2256_paper_route_current_sim_offtrack_failure_slice_diagnosis/failure_slice_routes.csv
```

Every output row must remain diagnostic:

```text
diagnostic_only: true
ranking_admissible: false
winner_selected: false
```

## Route Rules

M2256 should choose one primary route and optional secondary routes:

```text
if offtrack increase is concentrated in early_offtrack or severe_overshoot:
  route to recovery/corridor curriculum redesign

if offtrack increase is concentrated in high_sideslip or recovery failure:
  route to stability/recovery objective redesign

if collision or negative_clearance_margin increases materially:
  route to collision/clearance guardrail repair

if one profile_seed group dominates the regression:
  route to profile-seed support audit before repair

if deltas are diffuse and no actionable slice dominates:
  route to branch synthesis or stop current-sim reward repair
```

Materiality threshold for route support:

```text
absolute count delta >= 5 episodes
or relative count increase >= 20% within the slice
```

## Guardrails

M2255 and M2256 must not:

```text
run environment reset
run environment rollout
execute policy actions
run measured execution
train
run replay
run PPO
use private holdout
promote any checkpoint
rank profiles
select a winner
claim finite-window-vs-GRU
claim level3 self-identification
claim paper-level result
```

## Next

Pre-register:

```text
m2256-paper-route-current-sim-offtrack-failure-slice-diagnosis-implementation
```
