# M1211 Paper-Route Corrected Profile Repeat Design

## Summary

M1211 pre-registers a fresh public repeat after M1210 audited M1209 as valid
but seed-fragile and insufficient for history/belief claims.

Decision:

```text
corrected_profile_repeat_design_admit_fresh_repeat_run
```

No controller training, PPO, candidate replay, promotion, private holdout, or
profile tuning occurs in M1211.

## Why Repeat

M1209 produced a useful corrected public pilot, but it is not stable enough to
scale:

```text
L3 family was strongest in aggregate.
L3_online_gru and L3_reset_control_corrected tied on success and termination.
L3 performance was dominated by one strong seed.
L2 normal did not beat current-tiled controls on safety margins.
```

The next question is repeatability, not longer training.

## Repeat Protocol

Use the same corrected profile set:

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

Use the same short public budget as M1209:

```text
training_seed_base: 111600
training_seed_offsets: [0, 1, 2]
eval_seed_base: 121600
eval_episodes_per_checkpoint: 64
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
device: cpu
vector_env_mode: sync
```

Run directory:

```text
runs/m1212_corrected_profile_repeat
```

The seed/eval blocks are public diagnostic blocks, not private holdout.

## Interpretation Rules

L2 finite-window history necessity:

```text
positive only if normal L2 beats current-tiled control on success by >= 0.03,
mean margin by >= 0.03, and does not increase collision by more than 0.02.
```

If success is slightly higher but margin/collision is worse, classify as:

```text
negative_or_inconclusive_for_finite_window_history_necessity
```

L3 recurrent-hidden benefit:

```text
positive only if L3_online_gru beats L3_reset_control_corrected on success by >= 0.05
or mean margin by >= 0.05 while not increasing collision by more than 0.02,
and the advantage appears in at least 2 of 3 training seeds.
```

If online and reset share the same strong/weak seeds, classify as:

```text
positive_for_L3_architecture_family
inconclusive_for_recurrent_hidden_benefit
```

No M1212 outcome may be called self-identification evidence. That requires later
matched-current, wrong-history, delayed-history, or reset/zero-response causal
gates.

## Route Rules

If M1212 matches M1209:

```text
route to combined corrected-pilot synthesis
```

If M1212 conflicts with M1209:

```text
route to seed-fragility audit
```

If M1212 shows online GRU beats corrected reset under the pre-registered
threshold:

```text
route to stronger history-causality gates
```

If M1212 again shows L2/current-tiled parity:

```text
stop treating L2 finite-window trend as history evidence and route to architecture/task redesign or synthesis
```

## Next Milestone

```text
experiments/manifests/m1212-paper-route-corrected-profile-repeat-run.json
```

M1212 may run the fresh repeat under the fixed protocol above. It must not
promote, use private holdout, tune per-profile settings, change actor inputs, or
claim paper-level/self-ID evidence.
