# M124 Retention-Calibrated Zero-Relvel Objective

M123 showed that M122 snippets are trainable, but the full M123 update
regressed yaw hidden-envelope lift. M124 tests whether a smaller
retention-calibrated update keeps the useful M122 objective signal and
zero-response behavior gap while preserving yaw belief.

## Sweep

Both candidates start from:

```text
runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt
```

and train on:

```text
runs/m122_zero_relvel_m105_strict_60ep_seed9720/outcome_intervention_snippets.npz
```

Candidate A:

```text
steps=80
learning_rate=0.00005
action_anchor_coef=20.0
seed=9820
run=runs/m124_calib_s80_lr5e5_anchor20_seed9820
```

Candidate B:

```text
steps=120
learning_rate=0.00005
action_anchor_coef=10.0
seeds=9821,9822,9823
runs=m124_calib_s120_lr5e5_anchor10_seed9821/9822/9823
```

## Objective Result

| Run | After loss | Improvement | After anchor MSE |
| --- | ---: | ---: | ---: |
| 80 steps, lr 5e-5, anchor 20, seed 9820 | 0.081277 | 0.005147 | 0.000055 |
| 120 steps, lr 5e-5, anchor 10, seed 9821 | 0.072802 | 0.013622 | 0.000368 |
| 120 steps, lr 5e-5, anchor 10, seed 9822 | 0.073205 | 0.013219 | 0.000328 |
| 120 steps, lr 5e-5, anchor 10, seed 9823 | 0.073274 | 0.013150 | 0.000336 |

Candidate A is too conservative. Candidate B keeps a repeatable M122 loss
improvement around `0.013` with low anchor MSE.

## Hidden-Envelope Probe

All probes use `configs/m121_human_view_zero_obstacle_relvel.json`, `30`
episodes, seed `9510`, horizon `15`, stride `3`, max samples `800`.

| Policy | Braking hidden-reset R2 | Lateral hidden-reset R2 | Yaw hidden-reset R2 |
| --- | ---: | ---: | ---: |
| M105 | -0.259482 | 0.368120 | 0.133647 |
| M123 9811 | -0.193512 | 0.442902 | 0.031559 |
| M124 9821 | -0.212614 | 0.543924 | 0.115071 |
| M124 9822 | -0.231874 | 0.554479 | 0.119341 |
| M124 9823 | -0.262513 | 0.534689 | 0.114265 |

Candidate B does not fully solve braking hidden-reset lift, but it avoids the
M123 yaw collapse. Yaw remains within about `0.014-0.020` of M105 instead of
dropping by about `0.102`.

## Behavior Gate

Primary behavior artifact:

```text
runs/m124_calib_s120_lr5e5_anchor10_behavior_gate_seed9500
```

Repeat normal-policy artifact:

```text
runs/m124_calib_s120_lr5e5_anchor10_repeat_behavior_seed9500
```

Selected behavior result:

| Policy | Success | Termination | Return mean | Clearance margin mean | Clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M105 | 0.8625 | 0.1375 | 65.548247 | 1.859915 | -0.115310 |
| M123 9811 | 0.8625 | 0.1375 | 65.595058 | 1.860069 | -0.156437 |
| M124 9821 | 0.8625 | 0.1375 | 65.630692 | 1.859754 | -0.125811 |
| M124 9821 reset | 0.8500 | 0.1500 | 63.861888 | 1.856561 | -0.169498 |
| M124 9821 zero-current | 0.8000 | 0.2000 | 60.444974 | 1.870999 | -0.148345 |
| M124 9821 zero-all | 0.8000 | 0.2000 | 60.444974 | 1.870999 | -0.148345 |
| M124 9821 no-action | 0.8625 | 0.1375 | 65.133026 | 1.862665 | -0.120653 |

Normal repeat behavior:

| Policy | Success | Clearance margin mean | Clearance margin min |
| --- | ---: | ---: | ---: |
| M105 | 0.8625 | 1.859915 | -0.115310 |
| M124 9821 | 0.8625 | 1.859754 | -0.125811 |
| M124 9822 | 0.8625 | 1.860271 | -0.124606 |
| M124 9823 | 0.8625 | 1.860539 | -0.124812 |

The calibrated recipe retains normal behavior and preserves the M123
zero-response behavior gap. No-action history is still neutral.

## Decision

M124 is a positive calibrated objective candidate, not a driver admission.

What improved versus M123:

- yaw hidden-envelope lift no longer collapses;
- normal behavior retention repeats across seeds `9821`, `9822`, and `9823`;
- zero-response behavior degradation remains visible for the selected 9821
  checkpoint;
- action-anchor MSE remains small.

Remaining blockers:

- M122 loss improvement is smaller than M123;
- braking hidden-reset lift remains negative;
- no-action history remains neutral;
- behavior and hidden probes still use one evaluation seed, so this needs a
  formal repeat gate before PPO.

The next step is M125: repeat M124 across behavior/probe seeds and stronger
history interventions before admitting the recipe for continuation.
