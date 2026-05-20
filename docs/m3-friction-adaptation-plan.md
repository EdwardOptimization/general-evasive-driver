# M3 Friction Adaptation Plan

Last updated: 2026-05-20

## Goal

M3 adds friction adaptation beyond the static circular-drift setting from M2.
The first target is friction-step circular tracking: the road friction changes
once during an episode, and the policy must keep tracking without privileged
access to the new friction value.

## Implemented Baseline

Friction-step evaluation config:

```text
configs/m3_friction_step_eval.json
```

This config enables:

- randomized initial `mu`, mass, CG, tire stiffness, and actuator lag;
- one friction change per episode at a seeded step in `[250, 550]`;
- post-step `mu` sampled from `[0.25, 1.15]`;
- speed-reference resampling after the friction step, still capped by the
  friction-limited circular speed.

Training templates:

```text
configs/ppo_m3_single_frame_friction_step.json
configs/ppo_m3_history_friction_step.json
configs/ppo_m3_privileged_friction_step.json
```

The single-frame config is the fine-tuning baseline. The history config is the
student-facing path. The privileged config is the teacher/reference path and
exposes hidden vehicle parameters including `mu`.

## M2 Checkpoint On M3 Task

Command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_circle_m2_seed113_recover2/checkpoint.pt \
  --env-config configs/m3_friction_step_eval.json \
  --run-dir runs/benchmark_m3_friction_step_m2_checkpoint_100eval
```

Overall result:

| policy | episodes | success_rate | return_mean | lateral_rmse_mean | beta_abs_error_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| checkpoint | 100 | 0.770 | 979.15 | 1.039 | 0.286 |
| heuristic | 100 | 0.080 | 231.21 | 1.918 | 0.479 |

Final-friction bucket result:

| policy | final mu bucket | episodes | success_rate | return_mean | lateral_rmse_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | low | 23 | 0.348 | 783.21 | 1.252 |
| checkpoint | medium | 46 | 0.826 | 991.74 | 1.063 |
| checkpoint | high | 31 | 1.000 | 1105.86 | 0.844 |

Initial-friction bucket result:

| policy | initial mu bucket | episodes | success_rate | return_mean | lateral_rmse_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | low | 26 | 1.000 | 1040.03 | 0.955 |
| checkpoint | medium | 34 | 0.824 | 1028.63 | 0.963 |
| checkpoint | high | 40 | 0.575 | 897.53 | 1.158 |

Interpretation:

- The M2 policy is strong when friction is static but not adaptive enough after
  a mid-episode transition.
- Failures concentrate when the final friction is low or when the episode
  starts high-mu and transitions downward.
- M3 should train on friction-step episodes and compare:
  single-frame policy, history-stacked policy, and privileged teacher policy.

## First M3 Training Attempts

Initial 1M-step M3 policies trained directly on the friction-step task did not
beat the M2 checkpoint baseline.

| run | observation | initialization | episodes | success_rate | return_mean |
| --- | --- | --- | ---: | ---: | ---: |
| `runs/benchmark_m3_friction_step_m2_checkpoint_100eval` | single-frame | M2 checkpoint, no M3 training | 100 | 0.770 | 979.15 |
| `runs/benchmark_ppo_m3_history_seed31_100eval` | history length 4 | scratch | 100 | 0.410 | 514.76 |
| `runs/benchmark_ppo_m3_privileged_seed37_100eval` | privileged params | scratch | 100 | 0.430 | 568.94 |
| `runs/benchmark_ppo_m3_single_frame_seed41_100eval` | single-frame | M2 checkpoint fine-tune | 100 | 0.730 | 952.85 |

Takeaway:

- Friction-step adaptation is not solved by simply adding history or privileged
  observations to a from-scratch PPO run.
- Directly fine-tuning the M2 policy on friction-step episodes also did not
  improve the benchmark.
- The next useful experiment is a staged M3 curriculum: static recovery,
  high/medium friction-step, low final-mu focus, then base friction-step
  recovery, mirroring the M2 low-mu/base recovery pattern.

## Exit Criteria

M3 should not be considered complete until:

- a non-privileged history or recurrent policy beats the M2 checkpoint on the
  friction-step benchmark;
- the same policy beats a single-frame policy trained on the same task;
- metrics are reported by initial and final `mu` bucket;
- selected friction-step rollouts include plots around the transition.
