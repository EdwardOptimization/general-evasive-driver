# M1197 Paper-Route Profile Training Smoke Stage B Run

## Summary

M1197 runs the bounded Stage B all-profile training smoke. All eight generated
controller profiles completed the same 1024-step CPU PPO plumbing run after
M1195 integrated controller-profile masks into train/eval vector paths.

This is still training-loop plumbing evidence only. It does not promote a
checkpoint, use private holdout, run candidate replay, tune profiles, claim
profile superiority, claim driver performance, or claim self-identification
evidence.

## Stage B Profiles

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
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
runs/m1197_profile_training_smoke_stage_b/summary.json
runs/m1197_profile_training_smoke_stage_b/profile_training_smoke_rows.csv
runs/m1197_profile_training_smoke_stage_b/<profile_name>/
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
result_class: profile_training_smoke_stage_b_pass
profile_count: 8
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
L2_window_13: return_mean=35.859060278934784, steps_mean=76.4, termination_rate=0.8
L2_window_25: return_mean=92.42838181199286, steps_mean=70.8, termination_rate=0.0
L2_window_50: return_mean=67.9624352218504, steps_mean=64.0, termination_rate=0.4
L2_window_100: return_mean=65.67843263045465, steps_mean=66.0, termination_rate=0.4
L3_online_gru: return_mean=39.381635195580216, steps_mean=64.6, termination_rate=0.6
L3_reset_control: return_mean=34.86279983247009, steps_mean=57.2, termination_rate=0.8
```

These values prove finite metrics and artifact integrity only. They are not a
fair performance comparison because this is one smoke seed per profile at 1024
steps.

## Commands

Representative command pattern:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo --config configs/paper_route_profiles/m1190_l2_window_100_smoke.json --run-dir runs/m1197_profile_training_smoke_stage_b/L2_window_100 --device cpu --vector-env-mode sync
```

The same command pattern was used for all generated smoke configs under:

```text
configs/paper_route_profiles/m1190_*_smoke.json
```

## Decision

```text
profile_training_smoke_stage_b_pass_route_to_fair_comparison_pilot_design
```

Stage B proves that all generated profile configs can complete smoke-scale
train-loop plumbing under the current code path. It admits a separate fair
comparison pilot design, not a performance claim or promotion.

## What Is Not Claimed

M1197 does not claim:

- any profile is better than another;
- any checkpoint is a driver candidate;
- any profile generalizes;
- GRU has recurrent-belief advantage;
- finite windows are sufficient;
- self-identification evidence;
- private-holdout readiness;
- paper-result readiness.
