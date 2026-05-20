# M14 Near-Threshold Training Plan

Last updated: 2026-05-21

## Motivation

M13 created the first behavior-critical paired gate: nominal success was 0.750
and perturbed success was 0.375 on a near-threshold seed corpus. However M11,
hidden-reset M11, and response-masked M11 all dropped by the same amount. The
gate is now strong enough; the current driver is not.

M14 changes the training distribution so the online recurrent actor repeatedly
sees near-threshold hidden-response cases.

## Environment Change

`ObstacleTaskConfig` now supports two training-only sampling filters:

- `max_threshold_score`: require a candidate obstacle to be close to the AES or
  drift lateral-capacity boundary;
- `min_time_after_friction_step`: require the friction perturbation to occur
  before the obstacle is reached.

These filters affect scenario sampling only. They are not actor observations.
The actor still receives the clean deployable frame plus its recurrent hidden
state.

## Training Config

Config:

```text
configs/ppo_m14_online_recurrent_near_threshold_driver.json
```

Key differences from M11:

- `actor_encoder="online_gru"`;
- `history_length=1`;
- `friction_step.enabled=true` with `step_range=[4, 16]`;
- initial road friction is sampled in a low-to-medium range so AEB-infeasible
  near-threshold geometry can be sampled strictly without fallback;
- post-step friction is randomized broadly;
- obstacle labels are restricted to non-AEB cases:
  `aes_feasible`, `drift_required`, and `unavoidable`;
- obstacle sampling uses `max_threshold_score=0.25` and
  `min_time_after_friction_step=0.10`.

There is no compatibility or best-effort fallback in this training path. If a
configuration cannot sample a matching scenario, reset fails and the
configuration must be fixed.

The first full CUDA attempt used `step_range=[8, 40]` and failed after 204,800
steps because a late friction step can make the strict non-AEB and
post-friction-obstacle filters geometrically incompatible for some seeds. The
fixed clean configuration moves the hidden perturbation earlier instead of
adding fallback sampling.

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m14_online_recurrent_near_threshold_driver.json \
  --seed 517 \
  --device cuda \
  --run-dir runs/ppo_m14_online_recurrent_near_threshold_seed517
```

## Validation

After training, re-run the exact M13 corpus:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv \
  --checkpoint runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt \
  --checkpoint-policy m14=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt \
  --checkpoint-policy m14_reset=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m14_zero_current=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt@zero_current_response \
  --checkpoint-policy m14_zero_all=runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m14_near_threshold_paired_gate_seed3000
```

Pass direction:

- improve perturbed success relative to M11 on the same corpus;
- show a measurable gap between normal M14 and `reset_recurrent_state`;
- keep nominal performance from regressing below M11.

If hidden reset remains equal to normal inference, M14 is a training-distribution
improvement only, not closed-loop self-identification proof.

## Result

Full CUDA training completed:

- checkpoint: `runs/ppo_m14_online_recurrent_near_threshold_seed517/checkpoint.pt`;
- final eval return mean: 53.519;
- final eval termination rate: 0.300.

M13 paired gate result:

| policy | nominal success | perturbed success | paired drop |
| --- | ---: | ---: | ---: |
| M14 | 0.600 | 0.300 | 0.300 |
| M14 reset hidden | 0.900 | 0.450 | 0.450 |
| M14 zero current response | 0.375 | 0.300 | 0.075 |
| M14 zero all response | 0.375 | 0.300 | 0.075 |

Interpretation: M14 did not pass the self-identification gate. Current response
features matter, but carried hidden state is harmful on this corpus because
resetting hidden state before every action outperforms normal recurrent
inference. The next clean fix is to remove the early-step training distribution
shift by sampling friction-step timing from accepted obstacle geometry.
