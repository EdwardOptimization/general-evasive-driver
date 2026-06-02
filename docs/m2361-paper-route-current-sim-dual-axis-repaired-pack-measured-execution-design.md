# M2361 Paper-Route Current-Sim Dual-Axis Repaired Pack Measured Execution Design

- status: completed
- decision: `repaired_pack_measured_execution_design_admit_pack_aware_runner`
- manifest: `experiments/manifests/m2361-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-design.json`
- parent audit: `docs/m2360-paper-route-current-sim-dual-axis-repaired-pack-reset-validation-result-audit.md`
- reset execution in M2361: `false`
- rollout/measured execution in M2361: `false`
- policy action executed in M2361: `false`
- training/replay/PPO: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2361 freezes a bounded measured-execution route for the M2359 reset-valid
repaired five-pack scenario family. It does not execute rollout. It only defines
the runner adapter, denominator, metadata, metrics, pass gates, and claim
boundary for M2362.

Input scenario family:

```text
repaired pack manifest:
  runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json

reset-validity evidence:
  runs/m2359_paper_route_current_sim_dual_axis_repaired_pack_reset_validation/summary.json

packs:
  baseline_reference_pack
  g_primary_pack
  h_primary_pack
  g_h_primary_pack
  gh_minimal_pack

scenario_specs_per_pack:
  72
```

## Runner Decision

The existing measured runner:

```text
autodrift.paper_route_current_sim_scenario_task_family_measured_execution
```

expects a single config containing `scenario_specs`. M2362 should implement a
pack-aware adapter:

```text
autodrift.paper_route_current_sim_dual_axis_repaired_pack_measured_execution
```

The adapter should reuse the existing episode mechanics and metrics from
`paper_route_current_sim_scenario_task_family_measured_execution`, including:

```text
load_actor_critic_checkpoint
build_env_config
ControllerProfileObservationWrapper / mask_spec_from_config
ActorPolicy
run_episode_with_policy
role success semantics
aggregate metric writers
```

but its workload should be generated from:

```text
repaired pack manifest from M2356
selected checkpoint rows from M2262
profile configs from the M2262 config root
```

## Checkpoint Source

Use the current-sim selected-checkpoint panel already used by M2293:

```text
selected rows:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv

config root:
  runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs
```

This source has:

```text
profiles: 5
seeds per profile: 3
selected checkpoint rows: 15
```

M2362 may aggregate by profile, profile-seed, pack, and repair class for
diagnostics, but it must not rank profiles, select a winner, promote a
checkpoint, or make a finite-window vs GRU claim.

## Execution Panel

Panel:

```text
config packs: 5
scenario specs per pack: 72
total scenario specs with pack identity: 5 * 72 = 360
selected checkpoints: 15
episodes: 5 * 72 * 15 = 5400
eval_seed_base: 236200
device: cpu
```

Seed rule:

```text
eval_seed =
  eval_seed_base
  + pack_index * 100000
  + selected_checkpoint_index * 1000
  + scenario_spec_index
```

This keeps each pack/checkpoint/spec cell deterministic and source-identifiable
without colliding across packs.

## Required Episode Metadata

Each episode row should include at least:

```text
pack_id
pack_index
pack_path
pack_is_baseline_reference
effective_selection_count
sampling_repair_fallback_count
scenario_index
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
sampling_repair_applied
sampling_repair_action
sampling_repair_class
sampling_repair_source_candidate_id
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

## Required Outputs

M2362 should write:

```text
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/summary.json
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/episode_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/failure_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/validation_failure_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/metadata_missing_rows.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/metric_completeness_failures.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/claim_boundary.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_pack.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_pack_profile.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_repair_class.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_role_family.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_scenario_family.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_profile_seed.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_profile.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_obstacle_label.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_timing_bucket.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_lateral_bucket.csv
runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution/aggregate_by_hidden_dynamics_bucket.csv
```

## Metrics And Aggregates

Use the existing M2293/M2307 metrics:

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

Do not interpret profile aggregates as a ranking in M2362. M2363 must audit
global and pack/role slices before any comparison or redesign decision.

## Frozen M2362 Command

M2362 should implement and run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_repaired_pack_measured_execution \
  --repaired-config-pack-manifest runs/m2356_paper_route_current_sim_dual_axis_candidate_pack_sampling_repair/repaired_config_pack_manifest.json \
  --selected-rows runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/selected_checkpoint_rows.csv \
  --config-root runs/m2262_paper_route_current_sim_midcourse_corridor_containment_training_execution/configs \
  --output-dir runs/m2362_paper_route_current_sim_dual_axis_repaired_pack_measured_execution \
  --eval-seed-base 236200 \
  --target-pack-count 5 \
  --target-scenario-specs-per-pack 72 \
  --target-selected-checkpoint-count 15 \
  --target-episode-count 5400 \
  --device cpu \
  --no-resume \
  --next-blocker m2363-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-result-audit
```

Focused tests should use a fake rollout function, not real environment rollout:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_repaired_pack_measured_execution.py
```

## Pass Gates

M2362 passes only if:

```text
summary.json exists
config_pack_count == 5
scenario_specs_per_pack_count == 72
selected_checkpoint_count == 15
episode_count == 5400
failure_count == 0
validation_failure_count == 0
metadata_missing_count == 0
metric_completeness_failure_count == 0
guardrail_violation_count == 0
controller_family_ranking_claim_made == false
support_policy_ranking_claim_made == false
winner_selected == false
paper_level_claim_made == false
finite_window_vs_gru_conclusion_made == false
level3_self_id_claim_made == false
scenario_redesign_executed_claim_made == false
```

Pass or fail, M2362 must route to M2363 result audit before interpretation.

## Claim Boundary

M2361 supports only:

```text
a bounded measured-execution design over the M2359 reset-valid repaired
five-pack scenario family.
```

M2362, if it passes, may claim only:

```text
the measured-execution panel completed and produced auditable outcome artifacts.
```

Still blocked until later audits:

```text
support-policy ranking;
controller-family ranking;
winner selection;
paper-level benchmark evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence;
scenario redesign executed.
```

## Next

Pre-register:

```text
m2362-paper-route-current-sim-dual-axis-repaired-pack-measured-execution-implementation
```
