# M8 Driver Gate Blocker Report

Last updated: 2026-05-21

## Status

Driver v1 is not passed.

The best current checkpoint is:

- `runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt`

It is the best M8 checkpoint because it improves aggregate obstacle-avoidance
success, keeps stable AES low-sideslip, and shows non-empty temporal latent
signal. It still fails the driver gate because behavior does not degrade when
history/action ablations are applied.

## Gate Evidence

Command:

```bash
conda run -n autodrift python -m autodrift.m7_gate \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --seed-csv runs/scenario_corpus_m7_aes_weighted_seed1300/scenario_corpus.csv \
  --episodes 60 \
  --seed 900 \
  --probe-episodes 100 \
  --probe-seed 1200 \
  --probe-epochs 160 \
  --device cpu \
  --run-dir runs/m8_driver_gate_seed227 \
  --driver-checkpoint runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt \
  --driver-name m8
```

Result:

| check | result |
| --- | --- |
| `success_beats_m5` | pass |
| `aes_feasible_sideslip_ok` | pass |
| `probe_temporal_lift_present` | pass |
| `ablation_drop_present` | fail |

Key metrics:

| metric | value |
| --- | ---: |
| M5 success | 0.700 |
| M7-A success | 0.700 |
| M7-B success | 0.700 |
| M8-A seed227 success | 0.733 |
| M8-A seed227 success delta vs M5 | 0.033 |
| M8-A seed227 `aes_feasible` high-sideslip | 0.038 |
| M8-A seed227 temporal-probe lift | 0.022 |
| M8-A seed227 ablation drop | 0.000 |

Label-bucket comparison:

| policy | `aes_feasible` success / high sideslip | `drift_required` success / high sideslip | `unavoidable` success |
| --- | --- | --- | ---: |
| M5 | 1.000 / 0.090 | 0.950 / 0.059 | 0.150 |
| M7-A | 1.000 / 0.292 | 0.950 / 0.079 | 0.150 |
| M7-B | 1.000 / 0.171 | 0.950 / 0.069 | 0.150 |
| M8-A seed227 | 1.000 / 0.038 | 0.950 / 0.024 | 0.250 |

## Negative Attempts

M8-A seed211:

- success improves to 0.733;
- temporal-probe lift is 0.022;
- `aes_feasible` high-sideslip is 0.159, slightly above the 0.150 threshold;
- ablation drop is 0.000.

M8-B temporal-GRU plus 6-step sequence head:

- success remains 0.733;
- `aes_feasible` high-sideslip rises to 0.165;
- temporal-probe lift drops to -0.005;
- ablation drop remains 0.000.

History-critical stress probe:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/m8_history_critical_obstacle_holdout_eval.json \
  --episodes 20 \
  --seed 1500 \
  --policies envelope_aes \
  --checkpoint-policy m5=runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --checkpoint-policy m8=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt \
  --checkpoint-policy m8_noact=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@zero_action_history \
  --checkpoint-policy m8_shuffle=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@shuffled_history \
  --checkpoint-policy m8_single=runs/ppo_m8_temporal_gru_driver_seed227/checkpoint.pt@single_frame_history \
  --device cpu \
  --run-dir runs/m8_history_critical_probe_seed1500
```

Result:

| policy | success | collision | high sideslip |
| --- | ---: | ---: | ---: |
| envelope AES | 0.400 | 0.600 | 0.000 |
| M5 | 0.300 | 0.700 | 0.028 |
| M8-A seed227 | 0.400 | 0.600 | 0.012 |
| M8 no action history | 0.400 | 0.600 | 0.014 |
| M8 shuffled history | 0.400 | 0.600 | 0.013 |
| M8 single-frame history | 0.400 | 0.600 | 0.016 |

This stress probe is harder, but it still does not make M8 behavior depend on
history.

M9 response-feature masking adds another negative result. On
`runs/research_m9_observation_degradation_gate`, M8 success remains 0.275 for
the base policy, `zero_current_response`, `zero_all_response`,
`single_frame_history`, and `shuffled_history`. Even all-response masking does
not change the aggregate success rate, so the benchmark still does not prove
closed-loop self-identification.

Follow-up observation-contract review found that the old obstacle frame also
included `aeb_stop_distance`, which is derived from hidden friction and braking
assumptions. This feature has been removed from actor observations. The M8
checkpoint is therefore a historical baseline, not the final driver-interface
baseline.

## Diagnosis

The current simulator and obstacle task are now good enough to measure stable
AES and drift-required obstacle avoidance, but they are not yet good enough to
prove professional-driver-like self-identification.

The likely reason is structural:

- the actor receives a very informative current frame: body velocities, yaw
  rate, sideslip estimate, steering state, drive/brake state, path frame, and
  obstacle-relative features;
- the actor also receives actuator state, so zeroing previous action commands
  does not remove all feedback about what the car is doing;
- obstacle episodes are short, so one-shot current-state feedback can be enough
  to match the baseline success rate;
- shuffled or repeated history changes the latent, but not enough to affect
  success on this corpus.

Therefore, aggregate success alone is not a sufficient proof of closed-loop
self-identification in this version of the task.

## Required Next Step

The next iteration should change the validation problem before another long
training run:

1. Add a formal history-critical driver-gate subset with delayed friction
   changes, actuator lag jumps, or online perturbations near obstacle approach.
2. Add a matching training augmentation or task curriculum so the actor has to
   use response history to infer controllability.
3. Consider a true online recurrent actor with carried hidden state, then add a
   hidden-state reset ablation in addition to stacked-history shuffling.
4. Keep M8-A seed227 as the current best checkpoint, but do not call it driver
   v1.

## Conclusion

M8 proves that recurrent/latent RL improves the current obstacle benchmark and
can reduce unnecessary stable-AES sideslip. It does not yet prove a general
professional-driver policy. Driver v1 remains blocked on behavior-level evidence
that closed-loop history changes the policy's decisions.
