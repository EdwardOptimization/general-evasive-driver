# M15 Obstacle-Aligned Perturbation Sampler

Last updated: 2026-05-21

## Motivation

M14 completed full training, but failed the M13 self-identification gate:
normal recurrent inference reached 0.600 nominal success and 0.300 perturbed
success, while hidden-reset inference reached 0.900 and 0.450. The actor uses
current response features, but carried hidden state is harmful on this corpus.

The likely distribution issue is that M14 fixed strict sampler failures by
moving friction steps early. That keeps training clean, but it no longer
matches the M13 gate's later hidden perturbation timing.

## Clean Sampler Change

When an obstacle task sets `min_time_after_friction_step`, the environment now
samples friction-step timing from the accepted obstacle geometry:

```text
accepted obstacle time_to_obstacle
  -> latest allowed friction_step_at
  -> sample within configured step_range
```

This is strict sampling, not fallback. If no step in the configured range can
satisfy the obstacle timing constraint, the candidate obstacle is rejected. The
actor still does not observe friction-step timing, true friction, labels, or
feasibility quantities.

## Training Config

Config:

```text
configs/ppo_m15_obstacle_aligned_recurrent_driver.json
```

Key difference from M14:

- `friction_step.step_range=[8, 40]`, matching the later perturbation timing
  used by the M13 gate;
- the sampler aligns the chosen step to obstacle time, so the strict non-AEB
  and post-friction-obstacle filters remain feasible.

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m15_obstacle_aligned_recurrent_driver.json \
  --seed 619 \
  --device cuda \
  --run-dir runs/ppo_m15_obstacle_aligned_recurrent_seed619
```

Smoke result:

- run dir: `runs/ppo_m15_obstacle_aligned_smoke`;
- eval return mean: 60.886;
- eval steps mean: 66.500;
- eval termination rate: 0.500;
- eval lateral RMSE mean: 0.348.

## Validation

Re-run the exact M13 paired corpus:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv \
  --checkpoint runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt \
  --checkpoint-policy m15=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt \
  --checkpoint-policy m15_reset=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m15_zero_current=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt@zero_current_response \
  --checkpoint-policy m15_zero_all=runs/ppo_m15_obstacle_aligned_recurrent_seed619/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m15_obstacle_aligned_paired_gate_seed3000
```

Pass direction:

- normal M15 should beat M14 on perturbed success;
- normal M15 should not be worse than hidden reset;
- response masking should remain worse than normal inference.
