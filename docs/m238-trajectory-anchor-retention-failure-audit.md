# M238 Trajectory-Anchor Retention Failure Audit

M238 audits why M237 still failed on-policy closed-loop proof retention even
after adding M235 trajectory action anchors. No PPO is run in this milestone.

Actor inputs are unchanged.

## Inputs

Parent checkpoints:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
runs/ppo_m237_trajectory_anchor_from_m224_seed5221/checkpoint.pt
```

Trajectory anchor:

```text
runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
```

M235 coverage:

| Source | Rows | Step range | Terminal margin |
| --- | ---: | --- | ---: |
| M183 M170 row 16 | 57 | 0-56 | 0.000106 |
| Protected key `9944|perturbed|28|28` | 40 | 0-39 | 0.186385 |

The failed M183 row and protected key are both covered by the trajectory anchor.

## Anchor-Matching Audit

M237 matches the M235 teacher-forced trajectory actions closely.

| Policy | Source | Rows | Action MSE mean | Action MSE max | Action L2 mean | Action L2 max |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| m224 | all | 97 | 0.000000000 | 0.000000000 | 0.000000132 | 0.000000347 |
| m237 | all | 97 | 0.000000398 | 0.000000799 | 0.001064 | 0.001548 |
| m237 | M183 row 16 | 57 | 0.000000275 | 0.000000340 | 0.000905 | 0.001010 |
| m237 | protected key | 40 | 0.000000573 | 0.000000799 | 0.001291 | 0.001548 |

Training also logged:

```text
trajectory_action_anchor_loss_mean = 0.000000134
```

So the failure is not missing anchor activation. The saved teacher-forced
states are being matched at the action level.

## Failed Proof Rows

M183 M170 still fails one row:

| Policy | Drops | Row 16 normal margin | Row 16 outcome |
| --- | ---: | ---: | --- |
| m224_10063 | 17 / 17 | 0.000106 | obstacle_completed |
| m233_5220 | 16 / 17 | -0.000169 | collision |
| m237_5221 | 16 / 17 | -0.000084 | collision |

M237 improves the failed row relative to M233 by about `0.000085`, but it is
still below the boundary. This is a near-zero-margin closed-loop sensitivity.

Protected key:

| Policy | Accepted | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | ---: | ---: | ---: |
| m224_10063 | 1 / 1 | 0.186385 | 0.086925 | 0.099460 |
| m233_5220 | 0 / 1 | 0.204645 | 0.104993 | 0.099652 |
| m237_5221 | 0 / 1 | 0.204386 | 0.104743 | 0.099643 |

M237 again improves slightly relative to M233, but it still leaves the existing
normal-margin window:

```text
0.204386 > 0.2
```

## Classification

The failure is not broad behavior collapse:

| Seed | M224 success | M237 success | M237 reset | M237 zero all |
| ---: | ---: | ---: | ---: | ---: |
| 9505 | 0.8625 | 0.8625 | 0.8500 | 0.8000 |
| 9506 | 0.8625 | 0.8625 | 0.8500 | 0.8000 |

The failure is also not simple coverage loss: M235 covers the exact failed row
and protected key. It is not simple teacher-forced action mismatch either:
action deltas on the anchor states are only about `0.001` L2.

Best classification:

```text
on-policy closed-loop distribution drift under an update that is still too large
for near-boundary proof windows
```

This is a trust-region and promotion-discipline problem first. Stronger action
anchors may help, but they still do not directly constrain terminal margin or
the recurrent hidden/state sequence reached on-policy.

## Decision

Keep current best:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Do not repeat or lengthen M237.

Next step:

```text
m239-m237-checkpoint-interpolation-retention-probe
```

M239 should do a bounded no-PPO interpolation sweep from M224 toward M237. If a
small alpha preserves M183 M170 and protected key while retaining some fixed
objective improvement, the failure is mostly update magnitude and line-search
promotion can be used. If every useful alpha fails, the next repair needs a
stronger on-policy margin-retention mechanism rather than more action anchoring.
