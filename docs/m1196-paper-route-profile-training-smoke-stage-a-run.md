# M1196 Paper-Route Profile Training Smoke Stage A Run

## Summary

M1196 runs the bounded Stage A profile training smoke after M1195 integrated
controller-profile masks into train/eval vector paths.

This is training-loop plumbing evidence only. It does not promote a checkpoint,
use private holdout, run candidate replay, tune profiles from early results,
claim profile superiority, claim driver performance, or claim
self-identification evidence.

## Stage A Profiles

```text
L0_current_masked
L1_one_step
L2_window_25
L3_online_gru
```

Budget:

```text
total_steps: 1024
rollout_steps: 64
num_envs: 2
update_epochs: 1
seed policy: generated profile config seeds, one seed per profile
device: cpu
vector_env_mode: sync
```

## Artifacts

```text
runs/m1196_profile_training_smoke_stage_a/summary.json
runs/m1196_profile_training_smoke_stage_a/profile_training_smoke_rows.csv
runs/m1196_profile_training_smoke_stage_a/L0_current_masked/
runs/m1196_profile_training_smoke_stage_a/L1_one_step/
runs/m1196_profile_training_smoke_stage_a/L2_window_25/
runs/m1196_profile_training_smoke_stage_a/L3_online_gru/
```

Each profile run directory contains:

```text
checkpoint.pt
config.json
train_metrics.csv
eval_summary.json
manifest.json
```

## Result

```text
result_class: profile_training_smoke_stage_a_pass
profile_count: 4
all_profiles_complete: true
all_eval_metrics_finite: true
l0_runtime_mask_metadata_present: true
training_started: true
optimizer_started: true
ppo_used: true
candidate_replay_started: false
private_holdout_used: false
promoted: false
actor_input_contract_changed: false
profile_superiority_claimed: false
driver_performance_claimed: false
```

Smoke eval diagnostics:

```text
L0_current_masked: return_mean=71.2942288064106, steps_mean=64.4, termination_rate=0.4
L1_one_step: return_mean=43.39796917910165, steps_mean=59.6, termination_rate=0.8
L2_window_25: return_mean=92.42838181199286, steps_mean=70.8, termination_rate=0.0
L3_online_gru: return_mean=39.381635195580216, steps_mean=64.6, termination_rate=0.6
```

These values are recorded only to prove finite metrics and artifact integrity.
They are not a fair performance comparison because this is one smoke seed per
profile at 1024 steps.

## Commands

Representative command pattern:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo --config configs/paper_route_profiles/m1190_l0_current_masked_smoke.json --run-dir runs/m1196_profile_training_smoke_stage_a/L0_current_masked --device cpu --vector-env-mode sync
```

The same command pattern was used for:

```text
configs/paper_route_profiles/m1190_l1_one_step_smoke.json
configs/paper_route_profiles/m1190_l2_window_25_smoke.json
configs/paper_route_profiles/m1190_l3_online_gru_smoke.json
```

## Caveat

`controller_profile_runtime` inside each train config records the profile-mask
contract metadata. M1196's aggregate summary records the run-level facts:

```text
training_started: true
optimizer_started: true
ppo_used: true
```

Do not read the profile metadata guard fields as the run-level training status.

## Decision

```text
profile_training_smoke_stage_a_pass_route_to_stage_b_full_profile_smoke
```

Stage A proves representative L0/L1/L2/L3 train-loop plumbing is functional
after mask integration. It admits Stage B full generated-profile smoke, still
with no performance or promotion claim.
