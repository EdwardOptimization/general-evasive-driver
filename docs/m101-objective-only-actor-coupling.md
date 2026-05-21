# M101 Objective-Only Actor Coupling

M101 tests the missing piece from M99/M100: whether the actor can be coupled to
the M98 hidden-envelope belief before another PPO continuation.

M98 learned a better recurrent response belief, but M99 showed that the actor
did not use it. M100 tried a short guarded PPO continuation and kept behavior,
but reset and zero-response ablations still did not hurt behavior. M101 therefore
removes PPO from the loop and optimizes only actor coupling on fixed rollout
batches.

## Implementation

Added:

```text
src/autodrift/actor_coupling_optimize.py
tests/test_actor_coupling_optimize.py
```

The optimizer starts from:

```text
runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt
```

It freezes all model parameters except:

```text
response_context_fusion
actor_mean
```

The response encoder and online GRU are left unchanged. For each fixed batch it
computes:

```text
normal actions: carried recurrent hidden
reset actions:  hidden reset every step
reference:      frozen M98 normal-history actions
```

The loss is:

```text
anchor_coef * mse(normal_action, reference_action)
+ contrast_coef * softplus(action_margin - ||normal_action - reset_action||)
```

This keeps normal-history actions close to M98 while pushing reset-hidden actions
away on the same sampled observations.

## Smoke

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.actor_coupling_optimize \
  --checkpoint runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 8 \
  --seed 9520 \
  --horizon-steps 10 \
  --sample-stride 4 \
  --max-samples 160 \
  --train-fraction 0.70 \
  --steps 20 \
  --batch-size 64 \
  --learning-rate 0.0001 \
  --anchor-coef 10.0 \
  --contrast-coef 1.0 \
  --action-margin 0.04 \
  --grad-clip-norm 1.0 \
  --device cpu \
  --run-dir runs/m101_actor_coupling_objective_smoke_seed9520
```

Smoke result:

| run | before test action distance | after test action distance | gain | after anchor MSE |
| --- | ---: | ---: | ---: | ---: |
| seed9520 | 0.328333 | 0.524130 | 0.195796 | 0.001281 |

## Formal Objective Runs

Common settings:

```text
episodes: 30
horizon_steps: 15
sample_stride: 3
max_samples: 800
train_fraction: 0.70
steps: 200
batch_size: 256
learning_rate: 0.0001
anchor_coef: 10.0
contrast_coef: 1.0
action_margin: 0.04
```

| seed | samples | before test distance | after test distance | gain | after anchor MSE | margin pass |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9530 | 720 | 0.294063 | 1.142021 | 0.847957 | 0.002609 | 0.962791 |
| 9531 | 714 | 0.367917 | 1.192211 | 0.824294 | 0.001083 | 1.000000 |
| 9532 | 713 | 0.358375 | 1.089249 | 0.730874 | 0.021291 | 0.865471 |

This is a strong fixed-batch objective pass: all three seeds increase
normal-vs-reset action distance while keeping normal actions anchored. Seed
9532 has a noticeably higher anchor MSE, so behavior gating remains mandatory.

## Behavior Gate

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 80 \
  --seed 9500 \
  --policies heuristic \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m98_9480=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --checkpoint-policy m101_9530=runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt \
  --checkpoint-policy m101_9531=runs/m101_actor_coupling_objective_seed9531/optimized_checkpoint.pt \
  --checkpoint-policy m101_9532=runs/m101_actor_coupling_objective_seed9532/optimized_checkpoint.pt \
  --checkpoint-policy m101_9530_reset=runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m101_9530_zero_current=runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m101_9530_zero_all=runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m101_9530_noact=runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m101_actor_coupling_behavior_gate_seed9500
```

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| m62_a250 | 0.8625 | 0.1375 | 64.154043 | 1.852887 | -0.106535 |
| m98_9480 | 0.8625 | 0.1375 | 65.524351 | 1.853319 | -0.115454 |
| m101_9530 | 0.8625 | 0.1375 | 65.908976 | 1.864457 | -0.111205 |
| m101_9531 | 0.8625 | 0.1375 | 65.914274 | 1.862171 | -0.115024 |
| m101_9532 | 0.8625 | 0.1375 | 66.019001 | 1.857441 | -0.115504 |
| m101_9530_noact | 0.8625 | 0.1375 | 64.733217 | 1.880105 | -0.113597 |
| m101_9530_reset | 0.7875 | 0.2125 | 61.985705 | 1.796021 | -0.156603 |
| m101_9530_zero_current | 0.7750 | 0.2250 | 61.059530 | 1.843689 | -0.145558 |
| m101_9530_zero_all | 0.7750 | 0.2250 | 61.059530 | 1.843689 | -0.145558 |

This is the first clear behavior-level dependence signal in the M98 branch:

```text
normal success:        0.8625
reset hidden success:  0.7875
zero response success: 0.7750
```

The no-action-history ablation does not reduce success, although it reduces
return. This means the signal is mainly from response hidden/current response,
not yet from previous-command history alone.

## Hidden-Envelope Probe

M101 was compared against the M98 probe baseline on the same seed:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_probe \
  --checkpoint runs/m101_actor_coupling_objective_seed9530/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9510 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --run-dir runs/m101_actor_coupling_hidden_envelope_probe_seed9510
```

| checkpoint | target | response minus reset R2 lift | policy-feature minus reset R2 lift |
| --- | --- | ---: | ---: |
| M98 | braking | 0.358433 | -0.107152 |
| M98 | lateral accel | 0.682472 | -0.214677 |
| M98 | yaw | -0.014135 | 0.059138 |
| M101 | braking | -0.411792 | -0.147409 |
| M101 | lateral accel | -0.148631 | 0.602730 |
| M101 | yaw | 0.160665 | 0.128448 |

The probe is mixed-negative relative to the M101 admission rule. Behavior now
depends on recurrent response information, but the original M98 response-hidden
envelope advantage is not retained on the new M101 rollouts for braking and
lateral targets.

## Decision

M101 is a mixed result:

- fixed-batch actor coupling works strongly;
- behavior retention passes on the 80-seed gate;
- reset and zero-response ablations finally reduce success;
- hidden-envelope retention fails for braking and lateral response;
- no-action-history dependence is still weak.

Do not promote M101 directly into a long PPO continuation.

The next step is M102: make actor coupling retention-aware. It should preserve
the M101 behavior-dependence signal while adding a hidden-envelope retention
gate or objective so the M98 braking/lateral response belief is not washed out
by changed closed-loop trajectories.
