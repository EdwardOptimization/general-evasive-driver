# M2243 Paper-Route Current-Sim Selected-Checkpoint Outcome Localization Design

- status: completed
- decision: `current_sim_selected_checkpoint_outcome_localization_design_admit_execution`
- manifest: `experiments/manifests/m2243-paper-route-current-sim-selected-checkpoint-outcome-localization-design.json`
- parent audit: `docs/m2242-paper-route-current-sim-training-stability-repair-result-audit.md`
- selected checkpoint source: `runs/m2241_paper_route_current_sim_training_stability_repair_execution/selected_checkpoint_rows.csv`

## Design Rationale

M2241/M2242 establish two facts:

```text
selected_beats_final_count: 12/15
selected_checkpoint_profile_floor_pass_count: 0
```

Checkpoint retention is useful, but not sufficient. The remaining evidence gap
is episode-level failure mode. Aggregate eval says a selected checkpoint failed,
but it does not say whether the failure is offtrack, collision, max-step
noncompletion, poor clearance, sideslip/spin, or delayed recovery.

The next step should therefore localize outcomes for the selected checkpoints
before reward/task/curriculum repair.

## Execution Scope

Use exactly the `15` selected checkpoint rows from M2241:

```text
5 profiles x 3 seeds = 15 selected checkpoints
episodes per selected checkpoint = 32
total episode rows = 480
eval seed per selected row = seed_id + 10000
```

This intentionally matches the M2241 public candidate-eval seed policy so the
localization explains the same readiness result. It is not a private holdout and
not paper-level comparison evidence.

## Episode Fields

M2244 should use the existing evaluation path that emits rich episode rows. At
minimum, each row must include:

```text
profile_name
seed_id
selected_checkpoint_step
selected_checkpoint_path
episode_seed
outcome_bucket
success / obstacle_completed
collision
termination_reason
truncated
return
steps
lateral_rmse
lateral_peak
beta_abs_error_mean
beta_abs_peak
high_sideslip_fraction
speed_mean
action_rate_mean
min_clearance_margin
min_clearance_margin_min or row-level margin
max_off_track_overshoot
off_track_severity_proxy
time_to_first_off_track_s
impact_speed_proxy
impact_severity_proxy
```

Simulator hidden parameters may be logged for diagnostics, but remain forbidden
actor inputs:

```text
mu
mass_scale
inertia_scale
cg_shift
tire_stiffness_scale
brake_scale
drive_scale
steer_tau_scale
drive_tau_scale
```

## Grouping Axes

Produce aggregate rows for:

```text
global
profile_name
profile_name + seed_id
profile_name + selected_checkpoint_step
outcome_bucket
termination_reason
selected_readiness_floor_pass
```

Each aggregate should report:

```text
episode_count
success_count / success_rate
collision_count / collision_rate
offtrack_count / offtrack_rate
max_step_noncompletion_count / rate
mean_return
mean_steps
mean_min_clearance_margin
min_min_clearance_margin
mean_max_off_track_overshoot
mean_time_to_first_off_track_s
mean_high_sideslip_fraction
mean_action_rate
dominant_failure_mode
diagnostic_only
ranking_admissible=false
winner_selected=false
```

Minimum support:

```text
profile+seed rows require exactly 32 episodes.
profile rows require exactly 96 episodes.
global row requires exactly 480 episodes.
```

## Failure-Mode Labels

Use deterministic labels:

```text
success_supported
offtrack_dominated_failure
collision_dominated_failure
max_step_noncompletion_dominated_failure
mixed_failure
low_support_or_incomplete
```

Dominance rule:

```text
If a failure bucket is >= 50% of non-success episodes, assign that bucket.
If success_count >= 2/3 of episodes, assign success_supported.
Otherwise assign mixed_failure.
```

## Guardrails

M2244 must not:

```text
train
alter checkpoints
alter actor inputs
drop selected checkpoints
drop seeds
rank profiles
select a winner
use private holdout
claim finite-window-vs-GRU
claim level3 self-identification
claim paper-level result
```

## Required Outputs

M2244 should write:

```text
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/summary.json
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/episode_rows.csv
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/profile_seed_aggregate.csv
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/profile_aggregate.csv
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/outcome_aggregate.csv
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/repair_route_candidates.csv
runs/m2244_paper_route_current_sim_selected_checkpoint_outcome_localization/run_state.json
```

## Route Logic

M2244 should not directly change training. It should choose a route:

```text
if offtrack_dominated:
  route to offtrack/recovery reward and task-corridor repair design

if collision_dominated:
  route to obstacle timing/clearance/collision-penalty repair design

if max_step_noncompletion_dominated:
  route to progress/mission-completion reward repair design

if mixed:
  route to task-curriculum stratification design

if support is incomplete:
  route to artifact/runner repair
```

## Follow-Up

Admit:

```text
m2244-paper-route-current-sim-selected-checkpoint-outcome-localization-implementation
```

M2244 may run the diagnostic public evaluation over selected checkpoints. It is
not a ranking or paper result.
