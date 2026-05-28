# M1206 Paper-Route Corrected Profile Pilot Design

## Summary

M1206 designs the corrected public profile pilot after the M1205 synthesis.

Decision:

```text
corrected_profile_pilot_design_admit_config_generation
```

No controller training, PPO, candidate replay, promotion, private holdout, or
profile tuning occurs in M1206.

## Corrected Profile Set

Run these profiles in the corrected public pilot:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Purpose:

| Profile | Purpose |
| --- | --- |
| `L0_current_masked` | current-only lower anchor |
| `L1_one_step` | one-step command-response feedback |
| `L2_window_13` | short finite-window policy |
| `L2_window_13_current_tiled` | same L2 capacity, older history removed |
| `L2_window_25` | representative stronger M1199 finite-window policy |
| `L2_window_25_current_tiled` | same L2 capacity, older history removed |
| `L3_online_gru` | online recurrent policy with persistent hidden state |
| `L3_reset_control_corrected` | same online GRU architecture with every-step reset enforced in evaluation |

The current-tiled controls are required. Without them, an L2 trend cannot be
interpreted as finite-window history use.

## Budget

Use the same short public scale as M1199 so the first corrected pilot isolates
control semantics rather than budget changes:

```text
training_seeds_per_profile: 3
training_seed_base: 110600
training_seed_offsets: [0, 1, 2]
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
device: cpu
vector_env_mode: sync
```

Public eval:

```text
eval_seed_base: 120600
eval_episodes_per_checkpoint: 64
eval_seed_policy: same 64 public eval seeds for every profile checkpoint
```

These are public diagnostic seeds, not private holdout.

## Required Evaluation Semantics

Evaluation must apply:

```text
controller_profile.history_transform = current_tiled
controller_profile.reset_hidden_policy
controller_profile.observation_mask
```

Specifically:

```text
L2_*_current_tiled: train and eval through current_tiled history transform.
L3_online_gru: carry recurrent hidden through the episode.
L3_reset_control_corrected: reset recurrent hidden before every action during eval.
```

If evaluation cannot enforce those semantics, the pilot is invalid and must
route back to implementation repair.

## Metrics

Record per profile and seed:

```text
success_rate
collision_rate
road_departure_rate
spin_or_unstable_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
termination_rate
control_smoothness
runtime_seconds
parameter_count
observation_dim
finite_metric_flags
```

Required artifacts:

```text
runs/m1208_corrected_profile_pilot/summary.json
runs/m1208_corrected_profile_pilot/profile_seed_rows.csv
runs/m1208_corrected_profile_pilot/eval_rows.csv
runs/m1208_corrected_profile_pilot/profile_aggregate.csv
docs/m1208-paper-route-corrected-profile-pilot-run.md
```

The exact run id may change if config generation needs an intermediate smoke.

## Allowed Claims After The Corrected Pilot

Allowed:

```text
corrected public pilot profile trend
whether L2 beats its current-tiled capacity control
whether L3 online beats corrected reset-control
whether a longer public pilot is justified
```

Not allowed:

```text
promotion
private-holdout evidence
paper-level architecture ranking
self-identification
real-vehicle transfer
```

## Next Milestone

```text
experiments/manifests/m1207-paper-route-corrected-profile-config-generation.json
```

M1207 should generate or materialize corrected profile configs and run config
contract checks before any corrected PPO pilot.
