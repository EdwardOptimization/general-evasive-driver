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
configs/ppo_m3_staged_single_frame_friction_step.json
configs/ppo_m3_history_friction_step.json
configs/ppo_m3_staged_history_friction_step.json
configs/ppo_m3_privileged_friction_step.json
```

The single-frame config is the fine-tuning baseline. The history config is the
student-facing path. The privileged config is the teacher/reference path and
exposes hidden vehicle parameters including `mu`.

Historical M3 runs used checkpoint shape expansion to initialize a
history-stacked policy from a single-frame checkpoint. That compatibility path
has been removed. Current runs load init checkpoints strictly; if the actor
observation contract changes, the policy must be retrained under the new
contract.

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
| `runs/benchmark_ppo_m3_staged_single_frame_seed43_100eval` | staged single-frame | M2 checkpoint fine-tune | 100 | 0.730 | 944.07 |

Takeaway:

- Friction-step adaptation is not solved by simply adding history or privileged
  observations to a from-scratch PPO run.
- Directly fine-tuning the M2 policy on friction-step episodes also did not
  improve the benchmark.
- A staged single-frame curriculum still did not improve the benchmark. Its
  final low-friction bucket was only `0.217` success, confirming that the
  remaining failure mode is low-mu recovery after the transition rather than
  general circular tracking.
- The next useful experiment is initialized history-stacked training: start from
  the M2 policy behavior, expose recent state/action history, and train on the
  staged M3 curriculum.

Staged curriculum templates now encode that next experiment:

- `configs/ppo_m3_staged_single_frame_friction_step.json`
- `configs/ppo_m3_staged_history_friction_step.json`

Validated smoke command for initialized history training:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m3_staged_history_friction_step.json \
  --init-checkpoint runs/ppo_circle_m2_seed113_recover2/checkpoint.pt \
  --total-steps 512 \
  --eval-episodes 1 \
  --run-dir runs/ppo_m3_staged_history_seed47_init_m2_smoke
```

## Initialized History M3 Result

Command:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m3_staged_history_friction_step.json \
  --init-checkpoint runs/ppo_circle_m2_seed113_recover2/checkpoint.pt \
  --run-dir runs/ppo_m3_staged_history_seed47_init_m2
```

Benchmark command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_m3_staged_history_seed47_init_m2/checkpoint.pt \
  --env-config configs/ppo_m3_staged_history_friction_step.json \
  --run-dir runs/benchmark_ppo_m3_staged_history_seed47_init_m2_100eval
```

Overall result:

| policy | episodes | success_rate | return_mean | lateral_rmse_mean | beta_abs_error_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| checkpoint | 100 | 0.810 | 845.84 | 0.687 | 0.482 |
| heuristic | 100 | 0.080 | 231.21 | 1.918 | 0.479 |

Comparison against the two relevant baselines:

| run | observation | initialization | episodes | success_rate | return_mean |
| --- | --- | --- | ---: | ---: | ---: |
| `runs/benchmark_m3_friction_step_m2_checkpoint_100eval` | single-frame | M2 checkpoint, no M3 training | 100 | 0.770 | 979.15 |
| `runs/benchmark_ppo_m3_staged_single_frame_seed43_100eval` | staged single-frame | M2 checkpoint fine-tune | 100 | 0.730 | 944.07 |
| `runs/benchmark_ppo_m3_staged_history_seed47_init_m2_100eval` | history length 4 | M2 checkpoint, current-frame weight transfer | 100 | 0.810 | 845.84 |

Final-friction bucket result:

| final mu bucket | episodes | success_rate | return_mean | lateral_rmse_mean |
| --- | ---: | ---: | ---: | ---: |
| low | 23 | 0.304 | 654.05 | 1.123 |
| medium | 46 | 0.935 | 902.73 | 0.588 |
| high | 31 | 1.000 | 903.72 | 0.511 |

Initial-friction bucket result:

| initial mu bucket | episodes | success_rate | return_mean | lateral_rmse_mean |
| --- | ---: | ---: | ---: | ---: |
| low | 26 | 0.962 | 872.55 | 0.558 |
| medium | 34 | 0.853 | 868.98 | 0.622 |
| high | 40 | 0.675 | 808.81 | 0.826 |

Selected rollout plots:

```text
runs/rollouts_ppo_m3_staged_history_seed47_init_m2
```

The selected seeds cover:

| seed | initial_mu | final_mu | friction_step_at | terminated | purpose |
| ---: | ---: | ---: | ---: | --- | --- |
| 7 | 0.989 | 0.748 | 289 | false | high-to-medium success |
| 37 | 0.308 | 0.423 | 255 | false | low-friction success |
| 46 | 0.948 | 0.345 | 320 | true | high-to-low failure |
| 76 | 1.120 | 0.252 | 517 | true | late high-to-very-low failure |

Interpretation:

- M3 first-pass adaptation is now better than the M2 static policy on the
  friction-step benchmark and better than a single-frame policy trained on the
  same staged task.
- The improvement comes mainly from medium final friction and high-initial
  downshift cases. It is not a complete low-mu recovery solution: final low-mu
  success remains weak at `0.304`, and lower than the static M2 checkpoint's
  `0.348` on the same final-mu bucket.
- The next M3 refinement should target severe high-to-low transitions directly,
  either with a harder low-final curriculum, explicit recovery reward terms, or
  a recurrent/latent-friction policy instead of fixed history stacking.

## Exit Criteria

M3 first pass is complete because:

- a non-privileged history policy beats the M2 checkpoint on the friction-step
  benchmark;
- the same policy beats a single-frame policy trained on the same task;
- metrics are reported by initial and final `mu` bucket;
- selected friction-step rollouts include plots with the transition marked.

Remaining M3 risk:

- severe final low-mu transitions are still not solved and should stay as a
  targeted improvement track while M4/M5 path and obstacle tasks are added.
