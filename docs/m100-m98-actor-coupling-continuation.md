# M100 M98 Actor-Coupling Continuation

M100 tests the first guarded attempt to make the actor use the M98 hidden
envelope belief.

M98 passed the objective-only hidden-envelope gate. M99 showed that M98 retains
behavior, but reset and zero-response ablations do not degrade behavior. The
actor has a useful recurrent belief, but does not depend on it.

## Config

Added:

```text
configs/ppo_m100_m98_actor_coupling_smoke.json
```

Key settings:

```text
init checkpoint: runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt
baseline anchor: runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt
learning_rate: 1e-6
freeze_log_std: true
response_prediction_aux_coef: 0.06
action_contrast_aux_coef: 0.001
action_contrast_margin: 0.05
baseline_action_anchor_coef: 1.0
baseline_action_anchor_negative_advantage_only: true
```

The actor input contract remains the no-wheel 72-value human-view observation.
No hidden physical parameters or oracle labels are added.

## Training Smoke

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m100_m98_actor_coupling_smoke.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 4100 \
  --device cuda \
  --init-checkpoint runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --run-dir runs/ppo_m100_m98_actor_coupling_smoke_seed4100 \
  --eval-episodes 4
```

The run loaded both checkpoints strictly:

```text
loaded_init_checkpoint=.../m98.../optimized_checkpoint.pt load_mode=strict
loaded_baseline_action_anchor=.../m62.../alpha_0_25.pt load_mode=strict
```

Smoke eval:

```text
return_mean = 83.746500
termination_rate = 0.0
```

## Behavior Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 80 \
  --seed 9500 \
  --policies heuristic \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m98_9480=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --checkpoint-policy m100_smoke=runs/ppo_m100_m98_actor_coupling_smoke_seed4100/checkpoint.pt \
  --checkpoint-policy m100_smoke_reset=runs/ppo_m100_m98_actor_coupling_smoke_seed4100/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m100_smoke_zero_current=runs/ppo_m100_m98_actor_coupling_smoke_seed4100/checkpoint.pt@zero_current_response \
  --checkpoint-policy m100_smoke_zero_all=runs/ppo_m100_m98_actor_coupling_smoke_seed4100/checkpoint.pt@zero_all_response \
  --checkpoint-policy m100_smoke_noact=runs/ppo_m100_m98_actor_coupling_smoke_seed4100/checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m100_m98_actor_coupling_smoke_gate_seed9500
```

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| m62_a250 | 0.8625 | 0.1375 | 64.154043 | 1.852887 | -0.106535 |
| m98_9480 | 0.8625 | 0.1375 | 65.524351 | 1.853319 | -0.115454 |
| m100_smoke | 0.8625 | 0.1375 | 65.491779 | 1.853920 | -0.113155 |
| m100_smoke_noact | 0.8625 | 0.1375 | 64.808900 | 1.861130 | -0.113483 |
| m100_smoke_reset | 0.8750 | 0.1250 | 65.848112 | 1.848168 | -0.081130 |
| m100_smoke_zero_current | 0.8750 | 0.1250 | 65.656576 | 1.850613 | -0.158072 |
| m100_smoke_zero_all | 0.8750 | 0.1250 | 65.656576 | 1.850613 | -0.158072 |

## Hidden-Envelope Probe

M100 was also compared against the M98 init checkpoint on the same probe seed:

```text
runs/m100_m98_baseline_hidden_envelope_probe_seed9510
runs/m100_smoke_hidden_envelope_probe_seed9510
```

| checkpoint | target | response minus reset R2 lift | response minus reset MAE lift |
| --- | --- | ---: | ---: |
| M98 | braking | 0.358433 | 0.010046 |
| M98 | lateral accel | 0.682472 | 0.102998 |
| M98 | yaw | -0.014135 | -0.003117 |
| M100 | braking | 0.271200 | -0.000617 |
| M100 | lateral accel | 0.438872 | 0.033125 |
| M100 | yaw | -0.032174 | -0.020875 |

## Interpretation

M100 is negative for actor coupling.

What worked:

- The training path runs from M98 with strict checkpoint loading.
- Behavior retention is acceptable: M100 matches M62 and M98 success on the
  80-seed behavior gate.
- The smoke does not immediately collapse driving behavior.

What failed:

- Reset and zero-response ablations still do not hurt behavior; they slightly
  improve success.
- The small action-contrast term does not create behavior-level dependence on
  recurrent history.
- The hidden-envelope probe is not improved by the PPO smoke. It weakens M98's
  braking and lateral lift and leaves yaw negative on the shared probe seed.

## Decision

Do not run a long version of this M100 recipe.

The next step should be objective-only actor-coupling before PPO:

```text
freeze or preserve M98 response encoder and GRU;
train only policy/fusion/action layers on fixed batches;
anchor normal-history actions to M98 or M62;
penalize reset/zero-response actions only on states where hidden belief is useful;
require action-dependence and hidden-envelope probes to pass before PPO.
```

The project now has a belief state; the missing piece is a reliable actor
coupling objective.
