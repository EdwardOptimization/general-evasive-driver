# M11 Online Recurrent Driver Plan

Last updated: 2026-05-21

## Purpose

M10 proved that a clean fixed-window temporal-GRU driver is not enough. Its
success rate stayed unchanged under single-frame, shuffled-history, current
response, and all-response ablations. M11 moves the driver toward an explicitly
carried recurrent state.

## Design

New actor encoder:

```text
current deployable frame + previous action + recurrent hidden state
  -> frame encoder
  -> GRUCell hidden update
  -> actor/critic heads
  -> current low-level action
```

The M11 training config uses `history_length=1`. Memory is no longer provided by
stacking four observation frames; it is carried in the actor hidden state and
reset on episode reset.

The first implementation intentionally keeps PPO simple. Rollout collection
stores the hidden state used for each action, and PPO evaluates the old action
under that stored hidden state. This does not yet backpropagate through long
time spans, but it establishes the stateful actor, checkpoint format, evaluator
path, and hidden-state ablation gate.

## New Gate

M11 adds checkpoint ablation:

- `reset_recurrent_state`: reset actor hidden state before every action.

If the policy really uses carried response memory, normal M11 should outperform
`reset_recurrent_state` on the history-critical obstacle benchmark. If both are
equal, the policy is still behaving like a memoryless/current-frame driver.

## Training Task

Queued task:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m11_online_recurrent_driver.json \
  --seed 411 \
  --device cuda \
  --run-dir runs/ppo_m11_online_recurrent_driver_seed411
```

Infrastructure smoke:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m11_online_recurrent_driver.json \
  --total-steps 512 \
  --rollout-steps 64 \
  --eval-episodes 2 \
  --device cpu \
  --run-dir runs/ppo_m11_online_recurrent_smoke
```

Result:

| metric | value |
| --- | ---: |
| return mean | 23.592 |
| steps mean | 32.500 |
| termination rate | 0.500 |
| lateral RMSE mean | 0.412 |

This is only an infrastructure check. It proves the stateful actor can train,
save, load, evaluate, and run the hidden-reset ablation path.

Validation after training:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --episodes 40 \
  --seed 1600 \
  --policies envelope_aes \
  --checkpoint-policy m11=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11_reset=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m11_zero_current=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_current_response \
  --checkpoint-policy m11_zero_all=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m11_online_recurrent_gate_seed1600
```

Smoke validation with the untrained 512-step checkpoint completed successfully
using `/tmp/autodrift_m11_online_recurrent_gate_smoke`. The smoke checkpoint
failed behaviorally, as expected; the purpose was only to verify that
`reset_recurrent_state` is executable.

Expected evidence:

- aggregate success and label-bucket success;
- hidden-reset success drop;
- current/all-response ablation drop;
- latent/probe comparison if the gate shows a nonzero behavior difference.

## Open Risks

- Stored-hidden PPO is a first recurrent baseline, not full BPTT.
- The current history-critical benchmark may still be too easy or too label
  dominated.
- A stronger paired perturbation gate may still be needed: identical obstacle
  geometry, different hidden road/actuator change after the first control
  actions.

## Full Training Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m11_online_recurrent_driver.json \
  --seed 411 \
  --device cuda \
  --run-dir runs/ppo_m11_online_recurrent_driver_seed411
```

Result:

| metric | value |
| --- | ---: |
| return mean | 13.208 |
| steps mean | 32.800 |
| termination rate | 0.700 |
| lateral RMSE mean | 0.565 |
| beta abs error mean | 0.191 |

## Hidden-State Gate Result

Command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --episodes 40 \
  --seed 1600 \
  --policies envelope_aes \
  --checkpoint-policy m11=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt \
  --checkpoint-policy m11_reset=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m11_zero_current=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_current_response \
  --checkpoint-policy m11_zero_all=runs/ppo_m11_online_recurrent_driver_seed411/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m11_online_recurrent_gate_seed1600
```

Aggregate result:

| policy | success | collision | return | high sideslip |
| --- | ---: | ---: | ---: | ---: |
| envelope AES | 0.225 | 0.775 | 6.662 | 0.000 |
| M11 | 0.275 | 0.725 | 10.574 | 0.003 |
| M11 reset recurrent state | 0.275 | 0.725 | 10.299 | 0.011 |
| M11 zero current response | 0.250 | 0.750 | 9.052 | 0.001 |
| M11 zero all response | 0.250 | 0.750 | 9.052 | 0.001 |

Label-bucket result:

| policy | label | episodes | success | collision | return |
| --- | --- | ---: | ---: | ---: | ---: |
| M11 | drift_required | 9 | 1.000 | 0.000 | 77.792 |
| M11 | unavoidable | 31 | 0.065 | 0.935 | -8.940 |
| M11 reset recurrent state | drift_required | 9 | 1.000 | 0.000 | 77.406 |
| M11 reset recurrent state | unavoidable | 31 | 0.065 | 0.935 | -9.183 |
| M11 zero current/all response | drift_required | 9 | 0.889 | 0.111 | 71.223 |
| M11 zero current/all response | unavoidable | 31 | 0.065 | 0.935 | -8.997 |

Conclusion: M11 is a valid online recurrent infrastructure baseline, but it is
not yet evidence of driver-like self-identification. Resetting recurrent state
does not reduce success. Removing current response reduces aggregate success
from 0.275 to 0.250, so current feedback matters slightly, but the carried
hidden state is not behavior-critical on this gate.

Next step: build a paired perturbation gate where static obstacle geometry is
held fixed and hidden road/actuator response changes after the first control
actions. The current gate is still too label dominated to prove professional
driver behavior.
