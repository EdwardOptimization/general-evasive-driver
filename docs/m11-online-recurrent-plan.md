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
