# M43 Action-Trajectory Intervention Diagnostics

Last updated: 2026-05-21

## Motivation

M42 showed that hidden-contrast loss can train and preserve aggregate success at
the early checkpoint, but it does not create hidden-swap outcome sensitivity.
The M42 gate only reported first-action distance, which is too narrow: a policy
can differ on the first action and then immediately converge back to the same
closed-loop behavior.

M43 extends the hidden-swap gate to measure action divergence over the whole
continuation.

## Implementation

`autodrift.hidden_swap_gate` now records these replay fields:

```text
action_trajectory_distance_mean
action_trajectory_distance_rms
action_trajectory_distance_max
action_trajectory_compare_steps
```

Each metric compares a variant's deterministic action sequence against the
normal continuation over the common prefix. The summary CSV aggregates the same
fields by source condition, variant, and match acceptance.

## Commands

M37_102:

```bash
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --episodes 80 \
  --seed 4200 \
  --device cpu \
  --run-dir runs/m43_m37_102_action_trajectory_gate_seed4200
```

M42_028:

```bash
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt \
  --episodes 80 \
  --seed 4200 \
  --device cpu \
  --run-dir runs/m43_m42_028_action_trajectory_gate_seed4200
```

## Perturbed Accepted Matches

Both runs accepted 73 / 80 visible matches.

| Checkpoint | Variant | Success | First action distance | Trajectory mean distance | Trajectory RMS distance | Trajectory max distance |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M37_102 | hidden_swap | 0.6849 | 0.029597 | 0.005528 | 0.008859 | 0.031880 |
| M37_102 | reset | 0.6575 | 0.209906 | 0.219339 | 0.224898 | 0.280733 |
| M37_102 | zero_response | 0.6575 | 0.113424 | 0.199217 | 0.207295 | 0.268625 |
| M42_028 | hidden_swap | 0.6712 | 0.030208 | 0.004872 | 0.008246 | 0.031702 |
| M42_028 | reset | 0.6575 | 0.191957 | 0.200152 | 0.205404 | 0.259158 |
| M42_028 | zero_response | 0.6438 | 0.105304 | 0.180518 | 0.187769 | 0.243691 |

Outcome changes on the same accepted seeds:

| Checkpoint | Reset | Zero-response | Hidden-swap |
| --- | ---: | ---: | ---: |
| M37_102 | 2 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |
| M42_028 | 1 unfavorable / 0 favorable | 2 unfavorable / 0 favorable | 0 |

## Conclusion

M43 explains why M42 did not pass the self-identification gate. Hidden-swap
changes the first action a little, but the mean trajectory action distance is
only about 0.005, roughly 40x smaller than reset or zero-response trajectory
distances. The policy quickly collapses back to the same closed-loop behavior
after hidden-swap.

The next training objective should target sustained closed-loop action
differences on matched latent-response cases, not just stochastic log-prob
contrast on rollout actions. M37_102 remains the current best checkpoint.
