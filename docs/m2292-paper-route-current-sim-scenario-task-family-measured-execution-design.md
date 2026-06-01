# M2292 Paper-Route Current-Sim Scenario Task-Family Measured Execution Design

- status: completed
- decision: `current_sim_scenario_task_family_measured_execution_design_admit_focused_runner`
- manifest: `experiments/manifests/m2292-paper-route-current-sim-scenario-task-family-measured-execution-design.json`
- parent audit: `docs/m2291-paper-route-current-sim-scenario-task-family-reset-filter-edge-repair-result-audit.md`
- reset execution in M2292: `false`
- rollout/measured execution in M2292: `false`
- policy actions executed in M2292: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2292 freezes the first measured-execution route for the reset-valid six-role
scenario task-family pack:

```text
scenario config:
  configs/paper_route_current_sim_scenario_task_family_v0.json

reset-validity evidence:
  runs/m2290_paper_route_current_sim_scenario_task_family_filter_edge_repair/reset_validation/summary.json

reset_success_count:
  72 / 72
```

This design does not run the measured execution. It only defines the panel,
runner, metrics, and claim boundary.

## Runner Decision

Existing current-sim measured runners are close but not a direct fit:

```text
paper_route_current_sim_selected_checkpoint_outcome_localization:
  consumes selected checkpoints and per-profile config roots, but not
  scenario_specs.

paper_route_current_sim_controlled_comparison_measured_runner:
  consumes executable_task_specs + workload rows, not the new role-family
  scenario_specs JSON.
```

M2293 should implement a focused adapter:

```text
autodrift.paper_route_current_sim_scenario_task_family_measured_execution
```

The adapter should reuse the existing episode mechanics:

```text
load_actor_critic_checkpoint
build_env_config
ControllerProfileObservationWrapper / mask_spec_from_config
ActorPolicy
run_episode_with_policy
```

but its workload should be generated from:

```text
scenario_specs from configs/paper_route_current_sim_scenario_task_family_v0.json
selected checkpoint rows from M2262
profile configs from the M2262 config root
```

## Checkpoint Source

Use the latest current-sim selected-checkpoint panel from the midcourse
corridor-containment branch:

```text
selected rows:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv

config root:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs
```

This source has:

```text
5 controller profiles
3 seeds per profile
15 selected checkpoint rows
```

M2293 may aggregate by profile and profile-seed for diagnostics, but it must not
rank profiles, select a winner, promote a checkpoint, or make a finite-window vs
GRU claim.

## Execution Panel

Panel:

```text
scenario specs: 72
selected checkpoints: 15
episodes: 72 * 15 = 1080
eval_seed_base: 229300
device: cpu
```

Seed rule:

```text
eval_seed = eval_seed_base + selected_checkpoint_index * 1000 + scenario_spec_index
```

This keeps each selected checkpoint's 72-spec panel deterministic and
source-identifiable.

## Required Episode Metadata

Each episode row should include at least:

```text
scenario_spec_id
scenario_family_id
role_family
sampled_obstacle_label
allowed_labels_metadata_only
same_scene_group_id
hidden_dynamics_bucket
obstacle_longitudinal_timing_bucket
obstacle_lateral_offset_bucket
initial_speed_mps
track_radius_m
track_width_m
profile_name
seed_id
selected_checkpoint_path
selected_checkpoint_step
selected_checkpoint_kind
eval_seed
outcome_bucket
success
collision
off_track
termination_reason
return
steps
min_clearance_margin
max_off_track_overshoot
time_to_first_off_track_s
high_sideslip_fraction
action_rate_mean
```

## Metrics And Aggregates

M2293 should write:

```text
summary.json
episode_rows.csv
failure_rows.csv
aggregate_by_role_family.csv
aggregate_by_scenario_family.csv
aggregate_by_profile_seed.csv
aggregate_by_profile.csv
aggregate_by_obstacle_label.csv
aggregate_by_timing_bucket.csv
aggregate_by_lateral_bucket.csv
aggregate_by_hidden_dynamics_bucket.csv
claim_boundary.csv
```

Metrics:

```text
success_count / success_rate
collision_count / collision_rate
offtrack_count / offtrack_rate
max_step_noncompletion_count / rate
other_failure_count / rate
mean_return
mean_steps
mean_min_clearance_margin
min_min_clearance_margin
mean_max_off_track_overshoot
mean_time_to_first_off_track_s
mean_high_sideslip_fraction
mean_action_rate
dominant_failure_mode
```

## M2293 Command

M2293 should implement and run exactly:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_scenario_task_family_measured_execution \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --selected-rows runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv \
  --config-root runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs \
  --output-dir runs/m2293_paper_route_current_sim_scenario_task_family_measured_execution \
  --eval-seed-base 229300 \
  --target-scenario-spec-count 72 \
  --target-selected-checkpoint-count 15 \
  --target-episode-count 1080 \
  --device cpu \
  --next-blocker m2294-paper-route-current-sim-scenario-task-family-measured-execution-result-audit
```

M2293 may add focused unit tests for the runner using fake episode runners, but
it must not alter the command after execution unless a result audit admits a
repair.

## Pass Gates

M2293 passes only if:

```text
summary.json exists
episode_count == 1080
scenario_spec_count == 72
selected_checkpoint_count == 15
failure_count == 0
metadata_missing_count == 0
metric_completeness_failure_count == 0
guardrail_violation_count == 0
controller_family_ranking_claim_made == false
winner_selected == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
```

Pass or fail, M2293 must route to M2294 result audit before interpretation.

## Claim Boundary

M2293 may claim only:

```text
measured execution completeness or failure over the reset-valid role-family
scenario pack.
```

It cannot claim:

- controller-family ranking;
- winner selection;
- finite-window vs GRU conclusion;
- paper-level result;
- level3 self-identification.

## Next

Pre-register:

```text
m2293-paper-route-current-sim-scenario-task-family-measured-execution-implementation
```
